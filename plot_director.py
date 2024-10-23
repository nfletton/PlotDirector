import ast
import curses
import os
import re
import sys
from enum import Enum
from time import sleep

import requests
from nextdraw import NextDraw

API_OPTION_CASTS = {
    'handling': [int],
    'speed_pendown': [int],
    'speed_penup': [int],
    'accel': [int],
    'pen_pos_down': [int],
    'pen_pos_up': [int],
    'pen_rate_lower': [int],
    'pen_rate_raise': [int],
    'model': [int],
    'penlift': [int],
    'homing': [bool],
    'port': [lambda x: x],
    'port_config': [int],
    'units': [int],
}

API_FUNC_CASTS = {
    'load_config': [lambda x: x],
    'update': [],
    'goto': [float, float],
    'moveto': [float, float],
    'lineto': [float, float],
    'go': [float, float],
    'move': [float, float],
    'line': [float, float],
    'penup': [],
    'pendown': [],
    'draw_path': [ast.literal_eval],
    'delay': [int],
    'block': [],
    'usb_command': [lambda x: x],
    'usb_query': [lambda x: x],
}

STATEMENT_SEPARATOR = "|"

ALIGNMENT_SVG = '<svg width="74mm" height="105mm" viewBox="0 0 74 105" xmlns="http://www.w3.org/2000/svg"><circle style="fill:none;stroke:#000;stroke-width:.2;stroke-dasharray:none" cx="37" cy="40.975" r="24.57"/><path style="fill:none;stroke:#000;stroke-width:.264583px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" d="M7.577 40.975h58.846M37 11.551v58.847"/></svg>'


def notify(message, webhook):
    if webhook:
        requests.post(f"{webhook}", data=message.encode(encoding='utf-8'))


def convert_params(conversions, func_name, params):
    if func_name in conversions:
        return [func(params[i]) for i, func in enumerate(conversions[func_name])]
    else:
        return params


class States(Enum):
    INITIALIZING = 1
    PAUSED = 2
    PLOTTING = 3
    CALIBRATING = 4
    FINISHED = 5
    QUIT = 6


class Events:
    A = ord('a')
    C = ord('c')
    P = ord('p')
    Q = ord('q')
    DEFAULT = ord('w')


class GuiData:
    def __init__(self):
        self.warnings = []
        self.help_text = []


class State:
    PWR_WARNING = "NextDraw power supply appears to be off."

    def __init__(self, nd):
        self.nd = nd
        self.help_text = []
        self.messages = []

    def on_event(self, event):
        pass

    def __str__(self):
        return self.__class__.__name__


class Initializing(State):
    def __init__(self, nd, options):
        super().__init__(nd)
        self.options = options

    def on_event(self, event):
        if self.init_plot():
            if self.has_power():
                # give a heads up that in paused state
                self.nd.moveto(5, 5)
                self.nd.moveto(0, 0)
                return States.PAUSED, []
            else:
                return States.FINISHED, [Initializing.PWR_WARNING]
        else:
            return States.FINISHED, []

    def init_plot(self, ):
        self.nd.interactive()
        for name, value in self.options.items():
            self.apply_option(name, value)
        return self.nd.connect()

    def apply_option(self, name, value):
        setattr(getattr(self.nd, 'options'), name, *value)

    def has_power(self):
        return True if int(self.nd.usb_query("QC\r").split(",")[1]) > 276 else False


class Plotting(State):
    def __init__(self, nd, definitions, commands):
        super().__init__(nd)
        self.definitions = definitions
        self.commands = commands
        self.help_text = ["Pause: p"]

    def on_event(self, event):
        self.messages = []
        match event:
            case Events.P:
                self.nd.moveto(0.0, 0.0)
                return States.PAUSED, ["Manually paused"]
            case Events.DEFAULT:
                if self.nd.connected and len(self.commands) > 0:
                    name, params = self.commands.pop(0)
                    match name:
                        case "pause":
                            self.nd.moveto(0.0, 0.0)
                            if params:
                                message = ' '.join(params)
                            else:
                                message = "Paused in script"
                            return States.PAUSED, [message]
                        case _:
                            self.process_statement(name, params)
                else:
                    self.nd.moveto(0.0, 0.0)
                    return States.FINISHED, ["Plot completed"]
        return None, []

    def process_definition(self, statements):
        for name, params in statements:
            self.process_statement(name, params)

    def process_statement(self, name, params):
        if name in self.definitions:
            self.process_definition(self.definitions[name])
            return

        if name in API_OPTION_CASTS:
            if hasattr(getattr(self.nd, "options"), name):
                self.set_option(name, params)
        else:
            if hasattr(self.nd, name):
                self.run_function(name, params)
            # todo: add warning

    def run_function(self, name, params):
        try:
            api_command = getattr(self.nd, name)
            if callable(api_command):
                api_command(*params)
            else:
                self.messages.append(f"Attribute {name} exists in API but is not callable.")
        except AttributeError as e:
            self.messages.append(f"Error: {e} - {name} not found in {self.nd}.")
        except TypeError as e:
            self.messages.append(f"TypeError executing command {name} with parameters {params}: {e}")
        except Exception as e:
            self.messages.append(f"Unexpected error executing command {name} with parameters {params}: {e}")

    def set_option(self, name, params):
        try:
            setattr(getattr(self.nd, 'options'), name, *params)
        except Exception as e:
            self.messages.append(f"Error setting option {name} with parameters {params}: {e}")


class Paused(State):
    def __init__(self, nd):
        super().__init__(nd)
        self.help_text = ["Plot: p", "Calibrate: c", "Quit: q"]

    def on_event(self, event):
        match event:
            case Events.P:
                return States.PLOTTING, []
            case Events.Q:
                return States.FINISHED, []
            case Events.C:
                # end interactive context
                self.nd.penup()
                self.nd.moveto(0, 0)
                self.nd.block()
                self.nd.disconnect()
                # begin plot context
                self.nd.plot_setup()
                return States.CALIBRATING, []
        sleep(1)
        return None, []


class Calibrating(State):
    STEP_SIZE = 0.1
    plot_commands = {
        curses.KEY_LEFT: ("walk_mmx", -STEP_SIZE),
        curses.KEY_RIGHT: ("walk_mmx", STEP_SIZE),
        curses.KEY_UP: ("walk_mmy", STEP_SIZE),
        curses.KEY_DOWN: ("walk_mmy", -STEP_SIZE)
    }

    def __init__(self, nd, options):
        super().__init__(nd)
        self.options = options
        self.help_text = ["Run offset test SVG: F2",
                          "Decrement x axis: Left",
                          "Increment x axis: Right",
                          "Increment y axis: Up",
                          "Decrement y axis: Down",
                          "Init. plotting: p"]

    def on_event(self, event):

        if event in self.plot_commands:
            self.execute_utility(self.plot_commands[event])
            return None, []
        elif event == curses.KEY_F2:
            self.plot_alignment_svg()
            return None, []
        elif event == Events.P:
            self.reset_home_position()
            return States.INITIALIZING, []
        sleep(0.5)
        return None, []

    def execute_utility(self, cmd):
        utility_cmd, dist = cmd
        self.nd.options.mode = "utility"
        self.nd.options.utility_cmd = utility_cmd
        self.nd.options.dist = dist
        self.nd.plot_run()

    def plot_alignment_svg(self):
        self.reset_home_position()

        self.nd.plot_setup(ALIGNMENT_SVG)
        self.nd.options.model = self.options['model'][0]
        self.nd.options.penlift = self.options['penlift'][0]
        self.nd.options.pen_pos_up = self.options['pen_pos_up'][0]
        self.nd.options.pen_pos_down = self.options['pen_pos_down'][0]
        self.nd.plot_run()

    def reset_home_position(self):
        self.nd.options.mode = "plot"
        self.nd.plot_setup()
        self.nd.options.model = self.options['model'][0]
        self.nd.plot_run()


class Finishing(State):
    def __init__(self, nd, webhook):
        super().__init__(nd)
        self.webhook = webhook
        self.help_text = ["Quit: q"]

    def on_event(self, event):
        if event == Events.Q:
            self.nd.moveto(0.0, 0.0)
            self.nd.disconnect()
            notify("Plot completed", self.webhook)
            return States.QUIT, []
        sleep(0.5)
        return None, []


class Quit(State):
    def __init__(self, nd):
        super().__init__(nd)

    def on_event(self, event):
        return None, []


class StateMachine:
    def __init__(self, filename, webhook):
        self.nd = NextDraw()
        self.raw_plot_data = self.read_plot_data(filename)
        self.options = self.extract_setup_options()
        self.definitions = self.extract_definitions()
        self.commands = self.extract_plot_commands()
        self.states = {
            States.PAUSED: Paused(self.nd),
            States.INITIALIZING: Initializing(self.nd, self.options),
            States.PLOTTING: Plotting(self.nd, self.definitions, self.commands),
            States.CALIBRATING: Calibrating(self.nd, self.options),
            States.FINISHED: Finishing(self.nd, webhook),
            States.QUIT: Quit(self.nd),
        }
        self.state = self.states[States.INITIALIZING]
        self.messages = []
        self.new_messages = False

    def on_event(self, event):
        next_state, messages = self.state.on_event(event)
        if messages:
            self.messages.extend(messages)
            self.new_messages = True
        else:
            self.new_messages = False
        if next_state is not None:
            self.state = self.states[next_state]
        return self.state

    def read_plot_data(self, filename):
        with open(filename, 'r') as file:
            return [re.split(r'\s+', line.strip()) for line in file if line.strip()]

    def extract_setup_options(self):
        options = {}
        for statement in self.raw_plot_data:
            if statement[1] != "END_OPTIONS":
                name = statement[0]
                options[name] = convert_params(API_OPTION_CASTS, name, statement[1:])
            else:
                self.raw_plot_data = self.raw_plot_data[len(options) + 1:]
                break
        return options

    def breakdown_into_statements(self, body):
        statements = []
        name = None
        params = []

        for statement in body:
            if name is None:
                name = statement
            elif statement == STATEMENT_SEPARATOR:
                statements.append((name, convert_params(API_FUNC_CASTS, name, params)))
                name, params = None, []
            else:
                params.append(statement)

        if name is not None:
            statements.append((name, convert_params(API_FUNC_CASTS, name, params)))

        return statements

    def extract_definitions(self):
        definitions = {}

        for statement in self.raw_plot_data:
            name = statement[1]
            body = statement[2:]
            if name == "END_DEFINITIONS":
                self.raw_plot_data = self.raw_plot_data[len(definitions) + 1:]
                break
            else:
                definitions[name] = self.breakdown_into_statements(body)

        return definitions

    def extract_plot_commands(self):
        commands = []

        for statement in self.raw_plot_data:
            name = statement[0]

            if name == '#':
                continue

            if len(statement) > 1:
                if name in API_OPTION_CASTS:
                    casts = API_OPTION_CASTS
                else:
                    casts = API_FUNC_CASTS
                params = convert_params(casts, name, statement[1:])
            else:
                params = []
            commands.append((name, params))

        return commands

    def __str__(self):
        return "Current state: " + str(self.state)


class PlotDirector:
    def __init__(self, filename, webhook):
        self.filename = filename
        self.webhook = webhook
        self.nd = NextDraw()
        self.resized_win = False

    def start(self, stdscr):
        stdscr.nodelay(True)

        status_win, warning_win = self.init_windows(stdscr)
        cursor_location = (0, 0)

        machine = StateMachine(self.filename, self.webhook)

        current_state = None
        new_state = machine.state
        while True:
            key_press = stdscr.getch()
            if key_press > 0:
                match key_press:
                    case curses.KEY_RESIZE:
                        self.resize_windows(stdscr, status_win, warning_win)
                        self.resized_win = True
                    case _:
                        # Send user character input as event to current state
                        new_state = machine.on_event(key_press)
            else:
                # Send 'do work' event to the current state
                new_state = machine.on_event(Events.DEFAULT)

            if isinstance(new_state, Quit):
                status_win.move(*cursor_location)
                break
            if new_state != current_state:
                current_state = new_state
                cursor_location = self.update_status_window(status_win, current_state)
            elif self.resized_win:
                cursor_location = self.update_status_window(status_win, current_state)
                self.update_warning_window(warning_win, machine.messages)
                self.resized_win = False
            if machine.new_messages:
                self.update_warning_window(warning_win, machine.messages)
            stdscr.move(*cursor_location)

    def init_windows(self, stdscr):
        status_win = curses.newwin(1,1,0,0)
        status_win.keypad(True)
        warning_win = curses.newwin(1,1,2,0)
        warning_win.keypad(True)
        self.resize_windows(stdscr, status_win, warning_win)
        return status_win, warning_win


    def resize_windows(self, stdscr, status_win, warning_win):
        y, x = stdscr.getmaxyx()

        col_1_size = (y, int(x / 2))
        col_2_size = (y, x - col_1_size[1])
        col_1_pos = (0, 0)
        col_2_pos = (0, col_2_size[1])
        win_1_size = (int(y / 2), col_1_size[1])
        win_2_size = (y - win_1_size[0], col_1_size[1])
        win_1_pos = (0, 0)
        win_2_pos = (win_1_size[0], 0)

        stdscr.clear()
        stdscr.refresh()
        status_win.clear()
        warning_win.clear()
        status_win.resize(win_1_size[0], win_1_size[1])
        warning_win.resize(win_2_size[0], win_2_size[1])
        warning_win.mvwin(win_2_pos[0], win_2_pos[1])
        status_win.box()
        warning_win.box()
        warning_win.refresh()
        status_win.refresh()
        self.resized_win = True

    def update_status_window(self, window, state):
        window.clear()
        window.addstr(
            1, 2,
            f"Current State: {state}"
        )
        for i, option in enumerate(state.help_text):
            window.addstr(
                3 + i, 4,
                option
            )
        y, x = window.getyx()
        window.addstr(y + 2, 2,'>>> ')

        window.box()
        window.refresh()
        return window.getyx()

    def update_warning_window(self, window, warnings):
        window.clear()
        for i, warning in enumerate(warnings):
            window.addstr(
                1 + i, 4,
                warning
            )
        window.box()
        window.refresh()


if __name__ == '__main__':
    command_file = sys.argv[1]
    if len(sys.argv) > 2:
        webhook_url = sys.argv[2]
    else:
        webhook_url = ""

    if os.path.isfile(command_file):
        director = PlotDirector(command_file, webhook_url)
        curses.wrapper(director.start)
    else:
        print(f"File '{command_file}' does not exist.")
    quit()

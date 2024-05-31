import ast
import curses
import io
import os
import re
import sys

from axidrawinternal.axidraw import requests
from pyaxidraw import axidraw

AXI_PARAM_CASTS = {
    'speed_pendown': [int],
    'speed_penup': [int],
    'accel': [int],
    'pen_pos_down': [int],
    'pen_pos_up': [int],
    'pen_rate_lower': [int],
    'pen_rate_raise': [int],
    'pen_delay_down': [int],
    'pen_delay_up': [int],
    'const_speed': [bool],
    'model': [int],
    'penlift': [int],
    'port': [int],
    'port_config': [int],

    'units': [int],

    'load_config': [lambda x: x],

    'goto': [float, float],
    'moveto': [float, float],
    'lineto': [float, float],
    'go': [float, float],
    'move': [float, float],
    'line': [float, float],
    'draw_path': [ast.literal_eval],
    'delay': [int],
    'usb_command': [lambda x: x],
    'usb_query': [lambda x: x],
}


def notify(message, webhook):
    if webhook:
        requests.post(f"{webhook}", data=message.encode(encoding='utf-8'))


def convert_params(conversions, f_name, string_params):
    if f_name in conversions:
        return [func(string_params[i]) for i, func in enumerate(conversions[f_name])]
    else:
        return []


class PlotDirector:
    def __init__(self, ad):
        self.ad = ad

    definitions = {}

    def process_function(self, command_parts):
        function_name = command_parts[0]
        try:
            if len(command_parts) > 1:
                params = convert_params(AXI_PARAM_CASTS, function_name, command_parts[1:])
            else:
                params = []

            axi_draw_function = getattr(self.ad, function_name)
            axi_draw_function(*params)
        except Exception as e:
            print(f"Error executing command {function_name}: {e}")

    def process_option(self, option_parts):
        if len(option_parts) > 1:
            option_name = option_parts[0]
            option_value = convert_params(AXI_PARAM_CASTS, option_name, option_parts[1:])[0]
            try:
                setattr(getattr(self.ad, 'options'), option_name, option_value)
            except Exception as e:
                print(f"Error setting option '{option_name} to '{option_value}': {e}")
        else:
            print("No option name/value pair specified")

    def process_definition(self, statement):
        name, _, commands = statement.partition(' ')
        self.definitions[name] = commands

    def process_statement(self, statement):
        if statement[0] == '#':
            print(statement)
            return
        statement_parts = re.split(r'\s+', statement)

        match statement_parts[0]:
            case 'def':
                self.process_definition(statement[4:])
            case 'options':
                self.process_option(statement_parts[1:])
            case _:
                if statement_parts[0] in self.definitions:
                    commands = self.definitions[statement_parts[0]]
                    self.process_definition_body(commands)
                else:
                    self.process_function(statement_parts)

    def process_definition_body(self, commands):
        for command in commands.split(r'\n'):
            statement = command.strip()
            if statement:
                self.process_statement(statement)

    def process_stream(self, screen, stream):
        curses.cbreak()
        screen.nodelay(True)

        for line in stream:
            # get key press

            key_press = screen.getch()

            # compare key press
            if key_press == ord('q'):
                print("You pressed a key!")

            statement = line.strip()
            if statement:
                self.process_statement(statement)

    def process_axidraw_file(self, axidraw_file, webhook=""):
        if os.path.isfile(axidraw_file):
            with open(axidraw_file, 'r') as file:
                curses.wrapper(self.process_stream, file)
            self.ad.moveto(0.0, 0.0)
            self.ad.disconnect()
            notify("Pen plot completed", webhook)
        else:
            print(f"File '{axidraw_file}' does not exist.")


def safe(ad):
    if input("Is the AxiDraw in the home position? (y/n): ").lower() != 'y':
        print("\n*** 1. Turn off AxiDraw power supply.          ***")
        print("*** 2. Move the carriage to the home position. ***")
        print("*** 3. Turn the power supply back on.          ***")
        return False
    has_power = True if int(ad.usb_query("QC\r").split(",")[1]) > 276 else False
    if not has_power:
        print("\n*** AxiDraw power supply appears to be off. ****")
    return has_power


if __name__ == '__main__':
    filename = sys.argv[1]
    if len(sys.argv) > 2:
        webhook_url = sys.argv[2]
    else:
        webhook_url = ""
    ad = axidraw.AxiDraw()
    ad.interactive()
    # hardcoded penlift due to an API issue https://discord.com/channels/634791922749276188/634791923554451457/1200499591670407378
    ad.options.penlift = 3
    connected = ad.connect()
    if connected:
        if safe(ad):
            director = PlotDirector(ad)
            director.process_axidraw_file(filename, webhook_url)
    else:
        print("AxiDraw not connected.")

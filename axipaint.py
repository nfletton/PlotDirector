import ast
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


# TODO: logging for command processing progression
# TODO: ability to stop a plot
# TODO: ability to start a plot part way through
# TODO: ability to pause a plot and restart
# TODO: improved commandline option processing
# TODO: webhook notification of plot stages

def notify(message, webhook):
    if webhook:
        requests.post(f"{webhook}", data=message.encode(encoding='utf-8'))


def convert_params(conversions, f_name, string_params):
    if f_name in conversions:
        return [func(string_params[i]) for i, func in enumerate(conversions[f_name])]
    else:
        return []


class AxiPaint:
    def __init__(self):
        self.ad = axidraw.AxiDraw()

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
        name = statement.split()[0]
        commands = statement.split(' ', 1)[1]
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
                    self.process_stream(io.StringIO(commands))
                else:
                    self.process_function(statement_parts)

    def process_stream(self, stream):
        for line in stream:
            statement = line.strip()
            if statement:
                self.process_statement(statement)

    def process_axidraw_file(self, axidraw_file, webhook=""):
        if os.path.isfile(axidraw_file):
            self.ad.interactive()
            self.ad.options.penlift = 3
            connected = self.ad.connect()
            if connected:
                with open(axidraw_file, 'r') as file:
                    self.process_stream(file)
                self.ad.moveto(0.0, 0.0)
                self.ad.disconnect()
                notify("Pen plot completed", webhook)
            else:
                print("AxiDraw not connected.")
        else:
            print(f"File '{axidraw_file}' does not exist.")


if __name__ == '__main__':
    filename = sys.argv[1]
    if len(sys.argv) > 2:
        webhook_url = sys.argv[2]
    else:
        webhook_url = ""
    axiPaint = AxiPaint()
    axiPaint.process_axidraw_file(filename, webhook_url)

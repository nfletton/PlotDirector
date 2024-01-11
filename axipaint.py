import ast
import os
import re
import sys

from axidrawinternal.axidraw import requests
from pyaxidraw import axidraw

ad = axidraw.AxiDraw()

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


def convert_params(conversions, f_name, string_params):
    if f_name in conversions:
        return [func(string_params[i]) for i, func in enumerate(conversions[f_name])]
    else:
        return []


def process_function(axi_draw_instance, command_parts):
    function_name = command_parts[0]
    try:
        if len(command_parts) > 1:
            params = convert_params(AXI_PARAM_CASTS, function_name, command_parts[1:])
        else:
            params = []

        axi_draw_function = getattr(axi_draw_instance, function_name)
        axi_draw_function(*params)
    except Exception as e:
        print(f"Error executing command {function_name}: {e}")


def process_option(axi_draw_instance, option_parts):
    if len(option_parts) > 1:
        option_name = option_parts[0]
        option_value = convert_params(AXI_PARAM_CASTS, option_name, option_parts[1:])[0]
        try:
            setattr(getattr(axi_draw_instance, 'options'), option_name, option_value)
        except Exception as e:
            print(f"Error setting option '{option_name} to '{option_value}': {e}")
    else:
        print("No option name/value pair specified")


def process_statement(axi_draw_instance, statement):
    if statement[0] == '#':
        print(statement)
    else:
        statement_parts = re.split(r'\s+', statement)

        match statement_parts[0]:
            case 'options':
                process_option(axi_draw_instance, statement_parts[1:])
            case _:
                process_function(axi_draw_instance, statement_parts)


def process_axidraw_file(axidraw_file, webhook_url=""):
    if os.path.isfile(axidraw_file):
        ad.interactive()
        connected = ad.connect()
        if connected:
            with open(axidraw_file, 'r') as file:
                for line in file:
                    statement = line.strip()
                    if statement:
                        process_statement(ad, statement)
            ad.moveto(0.0, 0.0)
            ad.disconnect()
        else:
            print("AxiDraw not connected.")
    else:
        print(f"File '{axidraw_file}' does not exist.")
    notify("Drawing completed", webhook_url)


def notify(message, webhook_url):
    if webhook_url:
        requests.post(f"{webhook_url}", data=message.encode(encoding='utf-8'))


if __name__ == '__main__':
    filename = sys.argv[1]
    if len(sys.argv) > 2:
        webhook_url = sys.argv[2]
    else:
        webhook_url = ""
    process_axidraw_file(filename, webhook_url)

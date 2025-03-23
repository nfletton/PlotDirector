import ast
import logging
import re
from concurrent import futures

import grpc
from nextdraw import NextDraw

# Import generated gRPC code
from plot import plot_service_pb2, plot_service_pb2_grpc

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


def cast_api_params(conversions, func_name, params):
    casts = conversions.get(func_name)
    if casts:
        return [cast(param) for cast, param in zip(casts, params)]
    return params


def breakdown_into_statements(body):
    """Break down a sequence of tokens into named statements with parameters.

    Args:
        body (list): List of tokens to process

    Returns:
        list: List of tuples (name, params) representing statements
    """
    statements = []
    name, params = None, []

    for statement in body:
        if name is None:
            name = statement
        elif statement == STATEMENT_SEPARATOR:
            statements.append((name, cast_api_params(API_FUNC_CASTS, name, params)))
            name, params = None, []
        else:
            params.append(statement)
    if name is not None:
        statements.append((name, cast_api_params(API_FUNC_CASTS, name, params)))
    return statements


def extract_definitions(raw_definitions):
    """Extract raw string definitions into name/body dictionary.

    Args:
        raw_definitions (list): List of definitions as strings

    Returns:
        dict: Dictionary mapping definition names to their command sequences
    """
    definitions = {}
    split_definitions = [re.split(r'\s+', line.strip()) for line in raw_definitions]
    for definition in split_definitions:
        name = definition[0]
        body = definition[1:]
        definitions[name] = breakdown_into_statements(body)
    return definitions


class PlotService(plot_service_pb2_grpc.PlotServiceServicer):
    def __init__(self):
        self.nd = None
        self.default_options = {}
        self.definitions = {}

    def InitializePlot(self, request, context):
        """RPC method to initialize NextDraw with configuration options and command definitions."""
        try:
            if self.initialize_plot(request.options, request.definitions):
                logging.info("NextDraw initialized and connected")
                return plot_service_pb2.CommandResponse(
                    success=True,
                    message="NextDraw initialized successfully"
                )
            else:
                logging.error("Failed to initialize and connect to NextDraw")
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Failed to initialize NextDraw: {str(e)}"
            )

    def extract_options(self, raw_options):
        options = {}
        parts = [re.split(r'\s+', line.strip()) for line in raw_options]

        for option in parts:
            name = option[0]
            if name in API_OPTION_CASTS:
                options[name] = cast_api_params(API_OPTION_CASTS, name, option[1:])
            else:
                logging.warning('Attempt to set invalid option %s with value(s) %s' % (name, option[1:]))
        # force millimeter units
        options['units'] = 2
        return options

    def initialize_plot(self, options=None, definitions=None):
        """Initialize NextDraw instance with optional configuration parameters and command definitions.

        Args:
            options (list[str], optional): List of options to set on NextDraw before connecting.
            definitions (list[str], optional): List of command definitions to process.
        """
        self.nd = NextDraw()
        self.nd.interactive()

        if options:
            self.default_options = self.extract_options(options)

        if definitions:
            # Process command definitions
            self.definitions = extract_definitions(definitions)

        self.setup_interactive_context()

        return self.nd.connect()

    def setup_interactive_context(self):
        self.nd.interactive()
        for name, value in self.default_options.items():
            if hasattr(self.nd.options, name):
                setattr(self.nd.options, name, *value)
            else:
                logging.warning(f"Option {name} not found in NextDraw options")
        return self.nd.connect()

    def HasPower(self, request, context):
        """RPC method to check if NextDraw has power."""
        try:
            if self.nd is None:
                return plot_service_pb2.HasPowerResponse(
                    has_power=False
                )

            return plot_service_pb2.HasPowerResponse(
                has_power=int(self.nd.usb_query("QC\r").split(",")[1]) > 276
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error checking power status: {str(e)}")
            return plot_service_pb2.HasPowerResponse(
                has_power=False
            )

    def Disconnect(self, request, context):
        """RPC method to disconnect from NextDraw."""
        try:
            if self.nd is None:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="NextDraw is not initialized, nothing to disconnect."
                )

            self.nd.disconnect()
            self.nd = None
            return plot_service_pb2.CommandResponse(
                success=True,
                message="Successfully disconnected from NextDraw"
            )
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Failed to disconnect from NextDraw: {str(e)}"
            )

    def PlotAlignmentSVG(self, request, context):
        """RPC method to plot the alignment SVG."""
        try:
            if self.nd is None:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="NextDraw is not initialized. Call InitializePlot first."
                )

            # Configure and plot the alignment SVG
            self.nd.plot_setup(ALIGNMENT_SVG)

            # Set required options if they exist in default_options
            required_options = ['model', 'penlift', 'pen_pos_up', 'pen_pos_down']
            for option in required_options:
                if option in self.default_options:
                    setattr(self.nd.options, option, *self.default_options[option])

            self.nd.plot_run()

            return plot_service_pb2.CommandResponse(
                success=True,
                message="Alignment SVG plotted successfully"
            )
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Failed to plot alignment SVG: {str(e)}"
            )

    def WalkHome(self, request, context):
        """RPC method to walk the home position in x or y axis."""
        MAX_STEP_SIZE = 0.1
        try:
            if self.nd is None:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="NextDraw is not initialized. Call InitializePlot first."
                )

            # Validate axis parameter
            if request.axis not in ['x', 'y']:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="Invalid axis. Must be 'x' or 'y'."
                )

            distance = round(request.distance, 2)
            # Validate distance parameter
            if distance < -MAX_STEP_SIZE or distance > MAX_STEP_SIZE:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message=f"Invalid distance of {distance}. Must be in range plus or minus {MAX_STEP_SIZE}mm."
                )

            # Prepare utility command based on axis
            utility_cmd = f"walk_mm{request.axis}"

            # Set up and execute the walk command
            self.nd.plot_setup()
            self.nd.options.mode = "utility"
            self.nd.options.utility_cmd = utility_cmd
            self.nd.options.dist = distance
            self.nd.plot_run()

            return plot_service_pb2.CommandResponse(
                success=True,
                message=f"Walked {request.axis} axis by {distance}mm"
            )
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Failed to walk home position: {str(e)}"
            )

    def ResetHomePosition(self, request, context):
        """RPC method to reset the home position."""
        try:
            if self.nd is None:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="NextDraw is not initialized. Call InitializePlot first."
                )

            # Reset home position
            self.nd.options.mode = "plot"
            self.nd.plot_setup()
            if 'model' in self.default_options:
                self.nd.options.model = self.default_options['model'][0]
            self.nd.plot_run()

            return plot_service_pb2.CommandResponse(
                success=True,
                message="Successfully reset home position"
            )
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Failed to reset home position: {str(e)}"
            )

    def RestoreInteractiveContext(self, request, context):
        """RPC method to restore the interactive context."""
        try:
            if self.nd is None:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="NextDraw is not initialized. Call InitializePlot first."
                )

            # Restore interactive context
            self.setup_interactive_context()

            return plot_service_pb2.CommandResponse(
                success=True,
                message="Successfully restored interactive context"
            )
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Failed to restore interactive context: {str(e)}"
            )

    def ProcessCommand(self, request, context):
        try:
            if self.nd is None:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message="NextDraw is not initialized. Call InitializePlot first."
                )

            # Parse command and parameters
            parts = re.split(r'\s+', request.command.strip())
            command = parts[0]
            params = parts[1:] if len(parts) > 1 else []

            # Check if this is a defined command
            if command in self.definitions:
                # Execute all commands in the definition
                for cmd_name, cmd_params in self.definitions[command]:
                    if cmd_name in API_OPTION_CASTS and hasattr(self.nd.options, cmd_name):
                        setattr(self.nd.options, cmd_name, *cmd_params)
                        self.nd.update()
                    elif hasattr(self.nd, cmd_name):
                        getattr(self.nd, cmd_name)(*cmd_params)
                return plot_service_pb2.CommandResponse(
                    success=True,
                    message=f"Defined command {command} executed successfully"
                )

            # Process command based on its type
            if command in API_OPTION_CASTS and hasattr(self.nd.options, command):
                # Handle option setting
                cast_params = cast_api_params(API_OPTION_CASTS, command, params)
                setattr(self.nd.options, command, *cast_params)
                self.nd.update()
                return plot_service_pb2.CommandResponse(
                    success=True,
                    message=f"Option {command} set successfully"
                )
            elif hasattr(self.nd, command):
                # Handle function calls
                if command in API_FUNC_CASTS:
                    cast_params = cast_api_params(API_FUNC_CASTS, command, params)
                    getattr(self.nd, command)(*cast_params)
                    return plot_service_pb2.CommandResponse(
                        success=True,
                        message=f"Command {command} executed successfully"
                    )
                else:
                    return plot_service_pb2.CommandResponse(
                        success=False,
                        message=f"Unknown command type: {command}"
                    )
            else:
                return plot_service_pb2.CommandResponse(
                    success=False,
                    message=f"Unknown command: {command}"
                )
        except Exception as e:
            return plot_service_pb2.CommandResponse(
                success=False,
                message=f"Error processing command: {str(e)}"
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    plot_service_pb2_grpc.add_PlotServiceServicer_to_server(
        PlotService(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("Server started on port 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()

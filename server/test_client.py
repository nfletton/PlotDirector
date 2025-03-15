import grpc
import logging
from plot import plot_service_pb2
from plot import plot_service_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = plot_service_pb2_grpc.PlotServiceStub(channel)

        # Initial configuration options
        init_options = [
            "model 2",
            "penlift 3",
            "units 2",
            "pen_pos_up 47",
            "pen_pos_down 33",
            "accel 50",
            "speed_pendown 10",
            "speed_penup 35"
        ]

        # Command definitions
        init_definitions = [
            "go_home moveto 0 0",
            "draw_square moveto 0 0 | lineto 10 0 | lineto 10 10 | lineto 0 10 | lineto 0 0",
        ]

        # Initialize NextDraw with configuration and definitions
        try:
            response = stub.InitializePlot(
                plot_service_pb2.InitializePlotRequest(
                    options=init_options,
                    definitions=init_definitions
                )
            )
            logging.info("Initializing plot")
            logging.info(f"Response: {response.message}")
            logging.info(f"Success: {response.success}\n")
            if not response.success:
                return

        except Exception as e:
            logging.error(f"Error initializing plot: {str(e)}")
            return

        # Check power after initialization
        try:
            response = stub.HasPower(plot_service_pb2.HasPowerRequest())
            logging.info("Checking power after initialization")
            logging.info(f"Has power: {response.has_power}\n")
        except Exception as e:
            logging.error(f"Error checking power: {str(e)}")
            return

        # Test drawing commands
        commands = [
            "penup",
            "moveto 20 20",
            "pendown",
            "lineto 40 40",
            "draw_path [[50,50],[70,50],[70,70],[50,70],[50,50]]",
            "penup",
            "moveto 100 100",  # Move to a clear area
            "pendown",
            "draw_square",     # Execute our defined square command
            "go_home"         # Execute our defined home command
        ]

        for command in commands:
            try:
                response = stub.ProcessCommand(
                    plot_service_pb2.CommandRequest(command=command)
                )
                logging.info(f"Command: {command}")
                logging.info(f"Response: {response.message}")
                logging.info(f"Success: {response.success}\n")
            except Exception as e:
                logging.error(f"Error processing command '{command}': {str(e)}")

        # Test plotting alignment SVG
        try:
            response = stub.PlotAlignmentSVG(plot_service_pb2.PlotAlignmentSVGRequest())
            logging.info("Plotting alignment SVG")
            logging.info(f"Response: {response.message}")
            logging.info(f"Success: {response.success}\n")
            if not response.success:
                return
        except Exception as e:
            logging.error(f"Error plotting alignment SVG: {str(e)}")
            return


        # Test walking home position
        try:
            # Walk in X axis
            response = stub.WalkHome(
                plot_service_pb2.WalkHomeRequest(axis='x', distance=0.1)
            )
            logging.info("Walking home position in X axis")
            logging.info(f"Response: {response.message}")
            logging.info(f"Success: {response.success}\n")

            # Walk in Y axis
            response = stub.WalkHome(
                plot_service_pb2.WalkHomeRequest(axis='y', distance=0.1)
            )
            logging.info("Walking home position in Y axis")
            logging.info(f"Response: {response.message}")
            logging.info(f"Success: {response.success}\n")
        except Exception as e:
            logging.error(f"Error walking home position: {str(e)}")
            return

        # Test resetting home position
        try:
            response = stub.ResetHomePosition(plot_service_pb2.ResetHomePositionRequest())
            logging.info("Resetting home position")
            logging.info(f"Response: {response.message}")
            logging.info(f"Success: {response.success}\n")
        except Exception as e:
            logging.error(f"Error resetting home position: {str(e)}")
            return

        # Disconnect from NextDraw
        try:
            response = stub.Disconnect(plot_service_pb2.DisconnectRequest())
            logging.info("Disconnecting from NextDraw")
            logging.info(f"Response: {response.message}")
            logging.info(f"Success: {response.success}\n")

            # Check power after disconnection
            try:
                response = stub.HasPower(plot_service_pb2.HasPowerRequest())
                logging.info("Checking power after disconnection")
                logging.info(f"Has power: {response.has_power}\n")
            except Exception as e:
                logging.error(f"Error checking power: {str(e)}")
        except Exception as e:
            logging.error(f"Error disconnecting from NextDraw: {str(e)}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()

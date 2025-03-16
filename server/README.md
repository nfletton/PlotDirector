# Plot Director Server

Plot Director Server is a simple gRPC wrapper around the NextDraw Interactive Python API. 
It provides an interface for the
[Plot Director Client](https://github.com/nfletton/PlotDirector/tree/master/client) GUI to send
plotter requests to the NextDraw Python API.


## Features
- Executes [NextDraw Python API](https://bantam.tools/nd_py) commands in string form via a gRPC interface.
- Supports the definition of reusable NextDraw API commands sequences for operations that may include:
  - drawing tool dipping and washing.
  - changing NextDraw options during plots. e.g drawing tool height and speed

## Usage
To use, create a Python virtual environment and run `pip install -r requirements.txt` to install 
required packages (currently only the NextDraw API)

To run Plot Director Server: 
```shell
python server.py
```
## Testing
Connect a NextDraw drawing machine to the test machine.

Run the server:
```shell
python server.py
```

Within `test_client.py` verify that the `init_options` for `model` and `penlift` 
are correctly for your model NextDraw/AxiDraw. 
See the [API reference](https://bantam.tools/nd_py/#options-general).

Run the tests that simulate a client of the API:
```shell
python test_client.py
```

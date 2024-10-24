# Plot Director

Plot Director is a process that consumes plotter commands from a text file generated by 
[OPENRNDR](https://github.com/openrndr/openrndr) and the add-on feature 
[OPENRNDR Plot](https://github.com/nfletton/openrndr-plot) and drives an AxiDraw/NextDraw 
plotter via its Python API.

## Features
- Executes [NextDraw Python API](https://bantam.tools/nd_py) commands contained in a text file
- Supports definition of reusable sets of API commands for operations such a paintbrush dipping and washing. 
- Notification of plot completion via a webhook
- Pausing plots for pen change
- Calibration of home position to allow pen alignment to be adjusted after pen changes.

## Usage
To use, create a Python virtual environment and run `pip install -r requirements.txt` to install 
required packages (currently only the NextDraw API)

To run Plot Director: 
```shell
python plot_director.py <path to command file> <optional webhook URL>
```

For example, to run one of the included command file examples from 
this directory in a Linux terminal, the run command would be:
```shell
python plot_director.py command_examples/inline_adjust_pen_height.txt https://ntfy.sh/<your topic> 
```

## Input File Format
Sample input files are contained in the [command_examples](command_examples) directory.

An input file consists of:
- **Comments**  
  Any line starting with a `#` is interpreted as a comment and ignored.
- **Three Sections**
  - API options—considered as the defaults, set before a `connect()` call and
    used for restoring defaults during the plot process.
  - Definitions—that define reusable sets of plot commands: e.g. brush refill or wash
  - Plot commands—that define the finished artwork.


### NextDraw Interactive API Options  
Any line in the input file beginning with the name of 
an [API Option](https://bantam.tools/nd_py/#setting-options) results in a call to the respective API call. 
If placed in the options section of the input file, the option is
set along with other default options before `connect()` calls. 

Options placed inline with the plot commands are set as they occur 
and are automatically followed by a call to `update()`
   
e.g. `pen_pos_down 30` results in a [call to](https://bantam.tools/nd_py/#pen_pos_down).


### NextDraw Interactive API Functions
Any line in the plot commands section of the input file beginning with the name of an 
[API Function](https://bantam.tools/nd_py/#functions-interactive) results in a call to the respective API call 
e.g. `draw_path [[20.0,20.0],[190.0,20.0],[190.0,128.0],[20.0,128.0],[20.0,20.0]]`
results in a [call to](https://bantam.tools/nd_py/#draw_path).

### Pause Command  
Any line in the plot commands section of the input file beginning with `pause ` 
causes processing of further commands to pause until 
the user enters the continue console command to resume the plot.

Any characters after the command name are interpreted as a message which is sent to the console 
and the optional webhook.

### Reusable Command Sequences
Lines starting with `def ` in the definitions section of the input file,
define reusable blocks of API commands. These are useful when 
repeated sequences of commands are required for 
tasks such as reloading or washing a paintbrush in a well. A simple definition
looks like `def repeat_me penup | moveto 100 100 | pendown | lineto 120 120`.
In this example the definition would be called with the line `repeat_me`.




# Plot Director

Plot Director is a process that consumes plotter commands from a text file generated by 
[OPENRNDR](https://github.com/openrndr/openrndr) and the add-on feature 
[OPENRNDR Plot](https://github.com/nfletton/openrndr-plot)

## Features
- Executes [AxiDraw Python API](https://axidraw.com/doc/py_api/) commands contained in a text file
- Supports definition of reusable sets of API commands for operations such a paintbrush dipping and washing. 
- Notification of plot completion via a webhook
- Pausing plots at predefined positions

## Usage
To use, create a Python virtual environment and run `pip install -r requirements.txt` to install 
required packages (currently only the AxiDraw API)

To run Plot Director: 
```shell
python plot_director.py <path to command file> <optional webhook URL>
```

For example, to run one of the included command file examples from 
this directory in a Linux terminal, the run command would be:
```shell
python plot_director.py command_examples/pendown_penup.txt
```
Note: If running the above command in a Pycharm terminal window, the New Terminal Beta needs
to be enabled in Pycharm  settings. If running the command from a Pycharm run configuration
the 'Emulate terminal in output console' option must be set.

## Command Input File Format
Sample input files can be found in the [command_examples](command_examples) directory.

A command file consists of:
- **Comments**  
  Any line starting with a `#` is interpreted as a comment.
- **AxiDraw Interactive API Options**  
  Any line beginning with `options` is interpreted as an 
  [API Option](https://axidraw.com/doc/py_api/#setting-options) and 
  results in a call to the respective API call 
  e.g. `options pen_pos_down 30` results in a [call to](https://axidraw.com/doc/py_api/#pen_pos_down).
- **AxiDraw Interactive API Functions**  
  Any line beginning with the name of an 
  [API Function](https://axidraw.com/doc/py_api/#functions-interactive)
  results in a call to the respective API call  
  e.g. `draw_path [[20.0,20.0],[190.0,20.0],[190.0,128.0],[20.0,128.0],[20.0,20.0]]`
  results in a [call to](https://axidraw.com/doc/py_api/#draw_path).
- **Pause Command**  
  Lines matching the word `pause` causes processing of further commands to halt until the 
  keyboard character 'c' is pressed to resume the plot.
- **Reusable Command Sequences**  
  Lines starting with `def ` define reusable blocks of API commands. 
  These can be useful where repeated sequences of commands are required for 
  tasks such as reloading or washing a paintbrush in a well. A simple definition
  looks like `def repeat_me penup | moveto 100 100 | pendown | lineto 120 120`.
  In this example the definition would be called with the line `repeat_me`.
  

## Issues
### Hardcoded penlift
The `penlift` [API option](https://axidraw.com/doc/py_api/#penlift) is hardcoded to the brushless servo
as this option cannot be set in the command text file due to a bug in the Python API. Edit the script if
necessary for your setup.

## Feature Wishlist
- pretty up the console output either with the existing curses package or urwid
- ability to halt a plot at any point and restart plot at another time from the halt point
- display of plot progression
  - distance traveled relative to total distance
  - time so far relative to total time estimate
- logging for command processing progression
- improved commandline option processing

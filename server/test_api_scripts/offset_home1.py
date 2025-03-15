#!/usr/bin/env python

# Demonstrate offsetting the home position when using the Python API interactive context.
# See discussion: https://discord.com/channels/634791922749276188/1283423850888958043

import sys
from nextdraw import NextDraw

if __name__ == '__main__':

    nd = NextDraw()

    nd.interactive()
    nd.options.model = 2
    nd.options.penlift = 3
    nd.options.units = 2
    nd.options.pen_pos_up = 47
    nd.options.pen_pos_down = 33

    connected = nd.connect()

    if not connected:
        print("Not connected to machine; exiting (1).")
        sys.exit()

    nd.draw_path([[0,0],[0,50],[50,50],[50,0],[0,0]])
    nd.moveto(0,0)
    nd.delay(2000)

    # end interactive context
    nd.disconnect()

    # begin plot context
    nd.plot_setup()

    # adjust xy position
    nd.options.mode = "utility"
    nd.options.utility_cmd = "walk_mmx"
    nd.options.dist = 1.0
    nd.plot_run()
    nd.options.utility_cmd = "walk_mmy"
    nd.options.dist = 1.0
    nd.plot_run()

    # plot an empty file to set home position to the current position
    nd.options.mode = "plot"
    nd.plot_setup()
    nd.options.model = 2
    nd.plot_run()

    # enter interactive context
    nd.interactive()
    nd.options.model = 2
    nd.options.penlift = 3
    nd.options.units = 2
    nd.options.pen_pos_up = 47
    nd.options.pen_pos_down = 33

    connected = nd.connect()

    if not connected:
        print("Not connected to machine; exiting. (2)")
        sys.exit()

    nd.draw_path([[0,0],[0,50],[50,50],[50,0],[0,0]])
    nd.moveto(0,0)
    nd.disconnect()

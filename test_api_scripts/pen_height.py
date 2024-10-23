#!/usr/bin/env python

# Demonstrates an issue raised here https://discord.com/channels/@me/997194995264139407/1265761624816615505

import sys
from nextdraw import NextDraw

nd1 = NextDraw()

nd1.interactive()
nd1.options.penlift = 3
nd1.options.model = 2
nd1.options.units = 2
nd1.options.homing = False

connected = nd1.connect()

if not connected:
    print("Not connected to machine; exiting.")
    sys.exit()

nd1.penup()
nd1.options.pen_pos_up = 60
nd1.update()
nd1.options.pen_pos_up = 40
nd1.update()
nd1.options.pen_pos_up = 60
nd1.update()

nd1.disconnect()

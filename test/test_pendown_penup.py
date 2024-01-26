from pyaxidraw import axidraw
ad = axidraw.AxiDraw()
ad.interactive()
ad.options.penlift = 3

if not ad.connect():
    quit()
ad.options.model = 2
ad.options.units = 2
ad.update()

ad.goto(50.0, 50.0)
ad.pendown()
ad.penup()
ad.goto(0, 0)
ad.disconnect()

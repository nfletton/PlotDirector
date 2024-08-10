from nextdraw import NextDraw
ad = NextDraw()
ad.interactive()

if not ad.connect():
    quit()
ad.options.model = 2
ad.options.units = 2
ad.options.penlift = 3
ad.update()

ad.goto(50.0, 50.0)
ad.pendown()
ad.penup()
ad.goto(0, 0)
ad.disconnect()

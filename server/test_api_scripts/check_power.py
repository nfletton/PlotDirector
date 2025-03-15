from nextdraw import NextDraw


if __name__ == '__main__':
    nd = NextDraw()
    nd.interactive()
    nd.options.model = 2
    nd.options.penlift = 3
    connected = nd.connect()
    if connected:
        p = nd.usb_query("QC\r").split(",")[1]
        if int(p) > 275:
            print(f"Power is good ({p})")
        else:
            print(f"Power is low ({p})")
        nd.disconnect()
    else:
        print("Plotter not connected.")


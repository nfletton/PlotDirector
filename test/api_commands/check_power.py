from pyaxidraw import axidraw


if __name__ == '__main__':
    ad = axidraw.AxiDraw()
    ad.interactive()
    connected = ad.connect()
    if connected:
        p = ad.usb_query("QC\r").split(",")[1]
        if int(p) > 275:
            print(f"Power is good ({p})")
        else:
            print(f"Power is low ({p})")
        ad.disconnect()
    else:
        print("AxiDraw not connected.")


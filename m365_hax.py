from py9b.link.bleak import BleakLink

from py9b.transport.base import BaseTransport as BT
from py9b.transport.packet import BasePacket as PKT
from py9b.transport.xiaomi import XiaomiTransport

from py9b.command.regio import ReadRegs

import time

link = BleakLink()
with link:
    devs = link.scan()
    print(devs)

    tran = XiaomiTransport(link)

    link.open(devs[0])

    data = tran.execute(ReadRegs(BT.ESC, 0x68, "<H"))[0]
    print("BLE version: %04x" % data)

    if data >= 0x81:
        print("Connected, fetching keys...")
        keys = link.fetch_keys()
        tran.keys = keys
        print("keys:", keys)

        # Recover longer keystream
        req = PKT(src=BT.HOST, dst=BT.BMS, cmd=0x01, arg=0x50, data=bytearray([0x20]))
        tran.send(req)
        resp = tran.recv()
        tran.keys += resp.data[9:]
        print("Got %d bytes of keystream" % (len(tran.keys),))

        data = tran.execute(ReadRegs(BT.ESC, 0x68, "<H"))
        print("Version reported after encryption: %04x" % data)

    data = tran.execute(ReadRegs(BT.ESC, 0x1A, "<H"))[0]
    print("ESC version: %04x" % data)
    data = tran.execute(ReadRegs(BT.BMS, 0x17, "<H"))[0]
    print("BMS version: %04x" % data)

    print("ESC Serial:", tran.execute(ReadRegs(BT.ESC, 0x10, "12s"))[0].decode())
    print("BMS Serial:", tran.execute(ReadRegs(BT.BMS, 0x10, "12s"))[0].decode())

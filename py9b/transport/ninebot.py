"""Ninebot packet transport"""
from struct import pack, unpack
from .base import checksum, BaseTransport as BT
from .packet import BasePacket


class NinebotTransport(BT):
    def __init__(self, link, device=BT.HOST):
        super(NinebotTransport, self).__init__(link)
        self.device = device

    def _wait_pre(self):
        while True:
            while True:
                c = self.link.read(1)
                if c == b"\x5A":
                    break
            while True:
                c = self.link.read(1)
                if c == b"\xA5":
                    return True
                if c != b"\x5A":
                    break  # start waiting 5A again, else - this is 5A, so wait for A5

    def receive(self):
        self._wait_pre()
        pkt = self.link.read(1)
        l = ord(pkt) + 6
        for i in range(l):
            pkt += self.link.read(1)
        ck_calc = checksum(pkt[0:-2])
        ck_pkt = unpack("<H", pkt[-2:])[0]
        if ck_pkt != ck_calc:
            print("Checksum mismatch !")
            return None
        return BasePacket(
            pkt[1], pkt[2], pkt[3], pkt[4], pkt[5:-2]
        )  # sa, da, cmd, arg, data

    def send(self, packet, **kwargs):
        pkt = (
            pack(
                "<BBBBB",
                len(packet.data),
                packet.src,
                packet.dst,
                packet.cmd,
                packet.arg,
            )
            + packet.data
        )
        pkt = b"\x5A\xA5" + pkt + pack("<H", checksum(pkt))
        self.link.write(pkt)


__all__ = ["NinebotTransport"]

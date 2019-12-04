"""Transport abstract class"""


def checksum(data):
    s = 0
    for c in data:
        s += c
    return (s & 0xFFFF) ^ 0xFFFF


class BaseTransport(object):
    MOTOR = 0x01
    ESC = 0x20
    BLE = 0x21
    BMS = 0x22
    EXTBMS = 0x23
    HOST = 0x3E

    DeviceNames = {
        MOTOR: "MOTOR",
        ESC: "ESC",
        BLE: "BLE",
        BMS: "BMS",
        EXTBMS: "EXTBMS",
        HOST: "HOST",
    }

    def __init__(self, link):
        self.link = link
        self.retries = 5

    def receive(self):
        raise NotImplementedError()

    def send_and_receive(self, request, retries=None):
        exc = None
        for n in range(retries or self.retries):
            try:
                self.send(request)
                response = self.receive()
                return response
            except Exception as e:
                print("Retry sending request... %s" % str(request))
                exc = e
                pass
        raise exc

    def send(self, src, dst, cmd, arg, data=bytearray()):
        raise NotImplementedError()

    def execute(self, command, retries=None):
        rsp = self.send_and_receive(command.request, retries)
        return command.handle_response(rsp)

    @staticmethod
    def GetDeviceName(dev):
        return BaseTransport.DeviceNames.get(dev, "%02X" % dev)


__all__ = ["checksum", "BaseTransport"]

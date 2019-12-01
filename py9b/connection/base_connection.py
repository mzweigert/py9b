
class BaseConnection(object):
    def __init__(self, transport, link, address):
        self.transport = transport
        self.link = link
        self.address = address

    def __enter__(self):
        link = None
        if self.link == 'bleak':
            from py9b.link.bleak import BLELink
            link = BLELink()
        elif self.link == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.link == 'serial':
            from py9b.link.serial import SerialLink
            link = SerialLink(timeout=1.0)

        link.__enter__()

        if not self.address:
            ports = link.scan()
            if not ports:
                raise Exception('No devices found')
            self.address = ports[0][1]

        link.open(self.address)

        transport = None
        if self.transport == 'ninebot':
            from py9b.transport.ninebot import NinebotTransport
            transport = NinebotTransport(link)
        elif self.transport == 'xiaomi':
            from py9b.transport.xiaomi import XiaomiTransport
            transport = XiaomiTransport(link)

            keys_exists = link.is_characteristic_keys_exists()
            if keys_exists:
                transport.keys = link.fetch_keys()
                transport.recover_keys()
                print('Keys recovered')

        self._transport = transport
        self._link = link

        return transport

    def __exit__(self, a, b, c):
        self._link.__exit__(a, b, c)

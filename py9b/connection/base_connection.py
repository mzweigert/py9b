from py9b.link.base import NoDeviceFoundException


class BaseConnection(object):
    def __init__(self, transport, link, address):
        self.transport = transport
        self.link = link
        self.address = address

    def __enter__(self):
        self._link = self.__init_link()

        self._link.__enter__()

        if not self.address:
            ports = self._link.scan()
            if not ports:
                self._link.close()
                raise NoDeviceFoundException('No devices found')
            self.address = ports[0][1]

        self._link.open(self.address)
        try:
            self._transport = self.__init_transport(self._link)
        except Exception as e:
            self._link.close()
            raise e

        return self._transport

    def __init_link(self):
        link = None
        if self.link == 'bleak':
            from py9b.link.bleak import BleakLink
            link = BleakLink()
        elif self.link == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.link == 'serial':
            from py9b.link.serial import SerialLink
            link = SerialLink(timeout=1.0)
        return link

    def __init_transport(self, link):
        transport = None
        if self.transport == 'ninebot':
            from py9b.transport.ninebot import NinebotTransport
            transport = NinebotTransport(link)
        elif self.transport == 'xiaomi':
            from py9b.transport.xiaomi import XiaomiTransport
            transport = XiaomiTransport(link)

            if self.link.startswith('ble') and link.is_characteristic_keys_exists():
                transport.keys = link.fetch_keys()
                transport.recover_keys()
                print('Keys recovered')
        return transport

    def __exit__(self, exc_type, exc_value, traceback):
        self._link.__exit__(exc_type, exc_value, traceback)
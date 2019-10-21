import click

from py9b.transport.base import BaseTransport as BT
from py9b.command.regio import ReadRegs

class Connection:
    def __init__(self, transport, link, address):
        self.transport = transport
        self.link = link
        self.address = address

    def __enter__(self):
        link = None
        if self.link == 'bleak':
            from py9b.link.bleak import BleakLink
            link = BleakLink()
        elif self.link == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.link == 'serial':
            from py9b.link.serial import SerialLink
            link = SerialLink()

        link.__enter__()

        if not self.address:
            ports = link.scan()
            if not ports:
                raise Exception('No devices found')
            self.address = ports[0]

        link.open(self.address)

        transport = None
        if self.transport == 'ninebot':
            from py9b.transport.ninebot import NinebotTransport
            transport = NinebotTransport(link)
        elif self.transport == 'xiaomi':
            from py9b.transport.xiaomi import XiaomiTransport
            transport = XiaomiTransport(link)

            if transport.execute(ReadRegs(BT.ESC, 0x68, "<H"))[0] > 0x081 and self.link.startswith('ble'):
                transport.keys = link.fetch_keys()
                transport.recover_keys()
                print('Keys recovered')

        self._transport = transport
        self._link = link

        return transport

    def __exit__(self, a, b, c):
        self._link.__exit__(a, b, c)

@click.group()
@click.option('--transport', default='ninebot')
@click.option('--link', default='bleak')
@click.option('--address', default=None)
@click.pass_context
def cli(ctx, transport, link, address):
    ctx.obj = Connection(transport, link, address)

@cli.command()
@click.pass_context
def info(ctx):
    with ctx.obj as tran:
        print('ESC S/N:       %s' % tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0].decode())
        print('ESC PIN:       %s' % tran.execute(ReadRegs(BT.ESC, 0x17, "6s"))[0].decode())
        print()
        #print('BMS S/N:       %s' % tran.execute(ReadRegs(BT.BMS, 0x10, "14s"))[0].decode())
        #print('ExtBMS S/N:    %s' % tran.execute(ReadRegs(BT.EXTBMS, 0x10, "14s"))[0].decode())
        print()
        print('BLE Version:   %04x' % tran.execute(ReadRegs(BT.ESC, 0x68, "<H")))
        print('ESC Version:   %04x' % tran.execute(ReadRegs(BT.ESC, 0x1A, "<H")))
        #print('BMS Version:   %04x' % tran.execute(ReadRegs(BT.BMS, 0x17, "<H")))
        print()
        print('Error code:    %d' % tran.execute(ReadRegs(BT.ESC, 0x1B, "<H")))
        print('Warning code:  %d' % tran.execute(ReadRegs(BT.ESC, 0x1C, "<H")))
        print()
        print('Total mileage: %s' % pp_distance(tran.execute(ReadRegs(BT.ESC, 0x29, "<L"))[0]))
        print('Total runtime: %s' % pp_time(tran.execute(ReadRegs(BT.ESC, 0x32, "<H"))[0]))
        print('Total riding:  %s' % pp_time(tran.execute(ReadRegs(BT.ESC, 0x34, "<H"))[0]))
        print('Chassis temp:  %d°C' % (tran.execute(ReadRegs(BT.ESC, 0x3e, "<H"))[0] / 10.0,))
        print()

def pp_distance(dist):
    if dist < 1000:
        return '%dm' % dist
    return '%dkm %dm' % (dist / 1000.0, dist % 1000)

def pp_time(seconds):
    periods = [
        ('year',        60*60*24*365),
        ('month',       60*60*24*30),
        ('day',         60*60*24),
        ('hour',        60*60),
        ('minute',      60),
        ('second',      1)
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%2s %s%s" % (period_value, period_name, has_s))

    return " ".join(strings)

if __name__ == '__main__':
    cli()

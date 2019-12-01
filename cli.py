import click
import time

from py9b.link.base import LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.command.regio import ReadRegs, WriteRegs
from py9b.connection.base_connection import BaseConnection

from time import sleep


@click.group()
@click.option('--transport', default='ninebot',
              help='Transport to use (one of xiaomi, ninebot)')
@click.option('--link', default='bleak',
              help='Link implementation to use (one of serial, tcp, bleak)')
@click.option('--address', default=None,
              help='Device address to use (dependent on link, defaults to automatic scan)')
@click.pass_context
def cli(ctx, transport, link, address):
    ctx.obj = BaseConnection(transport, link, address)


@cli.command()
@click.option('--device', default='esc', help='Which device to dump (one of esc, ble, bms, extbms)')
@click.pass_context
def dump(ctx, device):
    dev = {
        'esc': BT.ESC,
        'ble': BT.BLE,
        'bms': BT.BMS,
        'extbms': BT.EXTBMS,
    }[device]
    with ctx.obj as tran:
        for offset in range(256):
            try:
                print('0x%02x: %04x' % (offset, tran.execute(ReadRegs(dev, offset, "<H"))[0]))
            except Exception as exc:
                print('0x%02x: %s' % (offset, exc))


@cli.command()
@click.pass_context
def sniff(ctx):
    with ctx.obj as tran:
        while True:
            try:
                print(tran.recv())
            except LinkTimeoutException as exc:
                pass
            except Exception as exc:
                print(exc)


@cli.command()
@click.pass_context
def powerdown(ctx):
    with ctx.obj as tran:
        tran.execute(WriteRegs(BT.ESC, 0x79, "<H", 0x0001))
        print('Done')


@cli.command()
@click.pass_context
def lock(ctx):
    with ctx.obj as tran:
        tran.execute(WriteRegs(BT.ESC, 0x70, "<H", 0x0001))
        print('Done')


@cli.command()
@click.pass_context
def unlock(ctx):
    with ctx.obj as tran:
        tran.execute(WriteRegs(BT.ESC, 0x71, "<H", 0x0001))
        print('Done')


@cli.command()
@click.pass_context
def reboot(ctx):
    with ctx.obj as tran:
        tran.execute(WriteRegs(BT.ESC, 0x78, "<H", 0x0001))
        print('Done')


def print_reg(tran, desc, reg, format, dev=BT.ESC):
    try:
        data = tran.execute(ReadRegs(dev, reg, format))
        print(desc % data)
    except Exception as exc:
        print(desc, repr(exc))


def bms_info(tran, dev):
    print('BMS S/N:         %s' % tran.execute(ReadRegs(dev, 0x10, "14s"))[0].decode())
    print_reg(tran, 'BMS Version:     %04x', 0x17, "<H", dev=dev)
    print_reg(tran, 'BMS charge:      %d%%', 0x32, "<H", dev=dev)
    print_reg(tran, 'BMS full cycles: %d', 0x1b, "<H", dev=dev)
    print_reg(tran, 'BMS charges:     %d', 0x1c, "<H", dev=dev)
    print_reg(tran, 'BMS health:      %d%%', 0x3b, "<H", dev=dev)
    print('BMS current:     %.2fA' % (tran.execute(ReadRegs(dev, 0x33, "<h"))[0] / 100.0,))
    print('BMS voltage:     %.2fV' % (tran.execute(ReadRegs(dev, 0x34, "<h"))[0] / 100.0,))


@cli.command()
@click.pass_context
def info(ctx):
    with ctx.obj as tran:
        while True:
            print('ESC S/N:       %s' % tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0].decode())
            print('ESC PIN:       %s' % tran.execute(ReadRegs(BT.ESC, 0x17, "6s"))[0].decode())
            print()
            print_reg(tran, 'BLE Version:   %04x', 0x68, "<H")
            print_reg(tran, 'ESC Version:   %04x', 0x1A, "<H")
            print()
            print_reg(tran, 'Error code:    %d', 0x1B, "<H")
            print_reg(tran, 'Warning code:  %d', 0x1C, "<H")
            print()
            print('Total mileage: %s' % pp_distance(tran.execute(ReadRegs(BT.ESC, 0x29, "<L"))[0]))
            print('Total runtime: %s' % pp_time(tran.execute(ReadRegs(BT.ESC, 0x32, "<L"))[0]))
            print('Total riding:  %s' % pp_time(tran.execute(ReadRegs(BT.ESC, 0x34, "<L"))[0]))
            print('Chassis temp:  %d C' % (tran.execute(ReadRegs(BT.ESC, 0x3e, "<H"))[0] / 10.0,))
            print()

            try:
                print(' *** Internal BMS ***')
                bms_info(tran, BT.BMS)
            except Exception as exc:
                print('No internal BMS found', repr(exc))

            sleep(3)


@cli.command()
@click.argument('new_sn')
@click.pass_context
def changesn(ctx, new_sn):
    from py9b.command.mfg import WriteSN

    with ctx.obj as tran:
        old_sn = tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0].decode()
        print("Old S/N:", old_sn)

        uid3 = tran.execute(ReadRegs(BT.ESC, 0xDE, "<L"))[0]
        print("UID3: %08X" % (uid3))

        auth = CalcSnAuth(old_sn, new_sn, uid3)
        # auth = 0
        print("Auth: %08X" % (auth))

        try:
            tran.execute(WriteSN(BT.ESC, new_sn.encode('utf-8'), auth))
            print("OK")
        except LinkTimeoutException:
            print("Timeout !")

        # save config and restart
        tran.execute(WriteRegs(BT.ESC, 0x78, "<H", 0x01))
        time.sleep(3)

        old_sn = tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0]
        print("Current S/N:", old_sn)


def pp_distance(dist):
    if dist < 1000:
        return '%dm' % dist
    return '%dkm %dm' % (dist / 1000.0, dist % 1000)


def pp_time(seconds):
    periods = [
        ('year', 60 * 60 * 24 * 365),
        ('month', 60 * 60 * 24 * 30),
        ('day', 60 * 60 * 24),
        ('hour', 60 * 60),
        ('minute', 60),
        ('second', 1)
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

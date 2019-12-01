import click

from time import sleep
from py9b.connection.xiaomi_ble_connection import XiaomiBLEBaseConnection, RecoveryEnergyMode


@click.group()
@click.option('--address', default=None,
              help='Device address to use (dependent on link, defaults to automatic scan)')
@click.pass_context
def cli(ctx, address):
    ctx.obj = XiaomiBLEBaseConnection(address)


def setters(obj):
    obj.set_cruise_control(True)
    print('Cruise on: %s' % obj.is_cruise_control_on())
    obj.set_cruise_control(False)
    print('Cruise on: %s' % obj.is_cruise_control_on())

    obj.set_tail_light(True)
    print('Tail light on: %s' % obj.is_tail_light_on())
    obj.set_tail_light(False)
    print('Tail light on: %s' % obj.is_tail_light_on())

    obj.set_recovery_energy(RecoveryEnergyMode.Weak)
    print('Recovery energy : %s' % obj.get_recovery_energy())

    obj.set_recovery_energy(RecoveryEnergyMode.Medium)
    print('Recovery energy : %s' % obj.get_recovery_energy())

    obj.set_recovery_energy(RecoveryEnergyMode.Strong)
    print('Recovery energy : %s' % obj.get_recovery_energy())


@cli.command()
@click.pass_context
def info(ctx):
    with ctx.obj as obj:
        while True:
            print('Total mileage: %s' % obj.get_total_mileage())
            print('Total runtime: %s' % obj.get_total_runtime())
            print('Total riding:  %s' % obj.get_total_riding())
            print('Chassis temp:  %d C' % obj.get_chassis_temp())
            print('Battery level: %d' % obj.get_battery_level())
            print('Speed:  %.2f' % obj.get_speed())

            setters(obj)

            print()

            sleep(1)


if __name__ == '__main__':
    cli()

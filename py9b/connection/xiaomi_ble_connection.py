import enum

from .base_connection import BaseConnection

from py9b.command.regio import ReadRegs, WriteRegs
from py9b.transport.base import BaseTransport as BaseTransport


def pp_distance(dist):
    if dist < 1000:
        return '%dm' % dist
    return '%dkm %dm' % (dist / 1000.0, dist % 1000)


class RecoveryEnergyMode(enum.Enum):
    Weak = 0
    Medium = 1
    Strong = 2


class XiaomiBLEBaseConnection(BaseConnection):
    def __init__(self, address=None):
        super(XiaomiBLEBaseConnection, self).__init__(transport="xiaomi", link="bleak", address=address)

    def __enter__(self):
        super(XiaomiBLEBaseConnection, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        super(XiaomiBLEBaseConnection, self).__exit__(exc_type, exc_value, traceback)

    def __execute_read_regs(self, reg_address, out_format):
        return self._transport.execute(ReadRegs(BaseTransport.ESC, reg_address, out_format))[0]

    def __execute_write_regs(self, reg_address, in_format, val):
        return self._transport.execute(WriteRegs(BaseTransport.ESC, reg_address, in_format, val))

    def get_total_mileage(self):
        return pp_distance(self.__execute_read_regs(0x29, "<L"))

    def get_total_runtime(self):
        return pp_distance(self.__execute_read_regs(0x32, "<L"))

    def get_total_riding(self):
        return pp_distance(self.__execute_read_regs(0x34, "<L"))

    def get_chassis_temp(self):
        return self.__execute_read_regs(0x3e, "<H") / 10.0

    def get_battery_level(self):
        return self.__execute_read_regs(0x22, "<H")

    def get_speed(self):
        speed = float(self.__execute_read_regs(0x26, "<H") / 1000.0)
        if 0.00 <= speed <= 35.00:
            return speed
        else:
            return 0

    def get_speed_mh(self):
        return self.__execute_read_regs(0xb5, "<H"),

    def power_down(self):
        self.__execute_write_regs(0x79, "<H", 0x0001)

    def lock(self):
        self.__execute_write_regs(0x70, "<H", 0x0001)

    def unlock(self):
        self.__execute_write_regs(0x71, "<H", 0x0001)

    def reboot(self):
        self.__execute_write_regs(0x78, "<H", 0x0001)

    def set_cruise_control(self, enable):
        if enable is True:
            self.__execute_write_regs(0x7c, "<H", 0x0001)
        else:
            self.__execute_write_regs(0x7c, "<H", 0x0000)

    def is_cruise_control_on(self):
        return self.__execute_read_regs(0x7c, "<H") == 0x0001

    def set_tail_light(self, enable):
        if enable is True:
            self.__execute_write_regs(0x7d, "<H", 0x0002)
        else:
            self.__execute_write_regs(0x7d, "<H", 0x0000)

    def is_tail_light_on(self):
        return self.__execute_read_regs(0x7d, "<H") == 0x0002

    def set_recovery_energy(self, mode):
        if mode == RecoveryEnergyMode.Weak:
            self.__execute_write_regs(0x7b, "<H", 0x0000)
        elif mode == RecoveryEnergyMode.Medium:
            self.__execute_write_regs(0x7b, "<H", 0x0001)
        elif mode == RecoveryEnergyMode.Strong:
            self.__execute_write_regs(0x7b, "<H", 0x0002)
        else:
            raise TypeError('mode must be an instance of RecoveryEnergyMode Enum')

    def get_recovery_energy(self):
        result = self.__execute_read_regs(0x7b, "<H")
        return RecoveryEnergyMode(result)


__all__ = ["XiaomiBLEBaseConnection", "RecoveryEnergyMode"]

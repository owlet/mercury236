import serial
import struct
import time
import argparse
from typing import Dict, ByteString


class EnergyMeter:
    """
    Класс для взаимодейстиия с ПУ Э/Э Меркурий 236
    """

    _energy_act: float = 0
    _energy_react: float = 0
    _pwr_act: float = 0
    _pwr_aL1: float = 0
    _pwr_aL2: float = 0
    _pwr_aL3: float = 0
    _pwr_react: float = 0
    _pwr_rL1: float = 0
    _pwr_rL2: float = 0
    _pwr_rL3: float = 0
    _pwr_seem: float = 0
    _pwr_sL1: float = 0
    _pwr_sL2: float = 0
    _pwr_sL3: float = 0
    _voltageL1: float = 0
    _voltageL2: float = 0
    _voltageL3: float = 0
    _currentL1: float = 0
    _currentL2: float = 0
    _currentL3: float = 0
    _freq: float = 0
    _cosf: float = 0

    port: serial.Serial = None

    # Команды отправляемые на port
    # Уже с контрольной суммой crc16 (два байта в конце)
    # Первый байт адрес ПУ (0 - broadcast)
    req: Dict[str, ByteString] = {
        "ID": bytearray(b"\x00\x08\x05\xb6\x03"),
        "Admin": bytearray(b"\x00\x01\x02\x02\x02\x02\x02\x02\x02\xb0\x07"),
        "Energy": bytearray(b"\x00\x05\x00\x00\x10%"),
        "VoltageL1": bytearray(b"\x00\x08\x11\x11M\xba"),
        "VoltageL2": bytearray(b"\x00\x08\x11\x12\r\xbb"),
        "VoltageL3": bytearray(b"\x00\x08\x11\x13\xcc{"),
        "TotalPowerActive": bytearray(b"\x00\x08\x11\x00\x8d\xb6"),
        "PowerActiveL1": bytearray(b"\x00\x08\x11\x01Lv"),
        "PowerActiveL2": bytearray(b"\x00\x08\x11\x02\x0cw"),
        "PowerActiveL3": bytearray(b"\x00\x08\x11\x03\xcd\xb7"),
        "TotalPowerReactive": bytearray(b"\x00\x08\x11\x04\x8cu"),
        "PowerReactiveL1": bytearray(b"\x00\x08\x11\x05M\xb5"),
        "PowerReactiveL2": bytearray(b"\x00\x08\x11\x06\r\xb4"),
        "PowerReactiveL3": bytearray(b"\x00\x08\x11\x07\xcct"),
        "TotalPowerSeem": bytearray(b"\x00\x08\x11\x08\x8cp"),
        "PowerSeemL1": bytearray(b"\x00\x08\x11\tM\xb0"),
        "PowerSeemL2": bytearray(b"\x00\x08\x11\n\r\xb1"),
        "PowerSeemL3": bytearray(b"\x00\x08\x11\x0b\xccq"),
        "CurrentL1": bytearray(b"\x00\x08\x11!M\xae"),
        "CurrentL2": bytearray(b'\x00\x08\x11"\r\xaf'),
        "CurrentL3": bytearray(b"\x00\x08\x11#\xcco"),
        "Frequency": bytearray(b"\x00\x08\x11@\x8cF"),
        "CosF": bytearray(b"\x00\x08\x160\x8f\x92"),
    }

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        parity: str = "N",
        bytesize: int = 8,
        stopbits: int = 1,
        timeout: float = 1.0,
    ):
        """
        Инициализация откртия порта с ПУ

        Args:
            port: Имя порта (unix: '/dev/ttyUSB0' windows: 'COM3')
            baudrate: Baud rate
            parity: Четность ('N', 'E', 'O')
            bytesize: Data bits
            stopbits: Stop bits
            timeout: Ожидание ответа (сек)
        """
        try:
            self.port = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=self._parse_parity(parity),
                bytesize=self._parse_bytesize(bytesize),
                stopbits=self._parse_stopbits(stopbits),
                timeout=timeout,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to open serial port {port}: {str(e)}")

    @staticmethod
    def _parse_parity(parity: str) -> serial.PARITY_NONE:
        """Конвертация переданного аргумента в константы serial.PARITY_*."""
        parity_map = {
            "N": serial.PARITY_NONE,
            "E": serial.PARITY_EVEN,
            "O": serial.PARITY_ODD,
        }
        return parity_map.get(parity.upper(), serial.PARITY_NONE)

    @staticmethod
    def _parse_bytesize(bytesize: int) -> int:
        """Проверка введенного bytesize"""
        if bytesize not in {5, 6, 7, 8}:
            raise ValueError("Bytesize must be 5, 6, 7, or 8")
        return bytesize

    @staticmethod
    def _parse_stopbits(stopbits: int) -> float:
        """Проверка введенного stopbits"""
        if stopbits not in {1, 2}:
            raise ValueError("Stopbits must be 1 or 2")
        return float(stopbits)

    def close(self) -> None:
        if self.port and self.port.is_open:
            self.port.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def cosf(self) -> float:
        """Cos(f) - Коэф. мощности"""
        return self._cosf

    @property
    def energy_act(self) -> float:
        """Активная энергия Вт*ч"""
        return self._energy_act

    @property
    def energy_react(self) -> float:
        """Реактивная энергия"""
        return self._energy_react

    @property
    def pwr_act(self) -> float:
        """Суммарная активная мощность Вт"""
        return self._pwr_act

    @property
    def pwr_aL1(self) -> float:
        """Активная мощность фаза A"""
        return self._pwr_aL1

    @property
    def pwr_aL2(self) -> float:
        """Активная мощность фаза B"""
        return self._pwr_aL2

    @property
    def pwr_aL3(self) -> float:
        """Активная мощность фаза C"""
        return self._pwr_aL3

    @property
    def pwr_react(self) -> float:
        """Суммарная реактивная мощность"""
        return self._pwr_react

    @property
    def pwr_rL1(self) -> float:
        """Реактивная мощность фаза A"""
        return self._pwr_rL1

    @property
    def pwr_rL2(self) -> float:
        """Реактивная мощность фаза B"""
        return self._pwr_rL2

    @property
    def pwr_rL3(self) -> float:
        """Реактивная мощность фаза C"""
        return self._pwr_rL3

    @property
    def pwr_seem(self) -> float:
        """Суммарная кажущаяся мощность"""
        return self._pwr_seem

    @property
    def pwr_sL1(self) -> float:
        """Кажущаяся мощность фаза A"""
        return self._pwr_sL1

    @property
    def pwr_sL2(self) -> float:
        """Кажущаяся мощность фаза B"""
        return self._pwr_sL2

    @property
    def pwr_sL3(self) -> float:
        """Кажущаяся мощность фаза C"""
        return self._pwr_sL3

    @property
    def voltageL1(self) -> float:
        """Напряжение фаза A"""
        return self._voltageL1

    @property
    def voltageL2(self) -> float:
        """Напряжение фаза B"""
        return self._voltageL2

    @property
    def voltageL3(self) -> float:
        """Напряжение фаза C"""
        return self._voltageL3

    @property
    def currentL1(self) -> float:
        """Ток фаза A"""
        return self._currentL1

    @property
    def currentL2(self) -> float:
        """Ток фаза A"""
        return self._currentL2

    @property
    def currentL3(self) -> float:
        """Ток фаза A"""
        return self._currentL3

    @property
    def freq(self) -> float:
        """Частота"""
        return self._freq

    def send(self, cmd: ByteString) -> bytearray:
        """
        Отправляет запросы на ПУ и в ответ получает bytearray
        """
        try:
            self.port.write(cmd)
            time.sleep(0.1)
            res = self.port.read(self.port.in_waiting)
            return bytearray(res)
        except serial.SerialException as e:
            raise ConnectionError(f"Communication error: {str(e)}")

    def read_data(self) -> None:
        """
        Чтение всех параметров из self.req
        """
        for param in self.req:
            try:
                payload = self.send(self.req[param])
                if not payload:
                    print(f"Ответа нет: {param}")
                    continue

                print(f"{param}: {payload}")

                if param == "Energy":
                    if len(payload) < 13:
                        print(f"Ошибка чтения {param} - ответ короткий")
                        continue

                    # Process active energy
                    rbAct = payload[1:5]
                    rbAct[0], rbAct[1], rbAct[2], rbAct[3] = (
                        rbAct[1],
                        rbAct[0],
                        rbAct[3],
                        rbAct[2],
                    )
                    self._energy_act = (struct.unpack(">I", rbAct)[0]) * 50

                    # Process reactive energy
                    rbReact = payload[9:13]
                    rbReact[0], rbReact[1], rbReact[2], rbReact[3] = (
                        rbReact[1],
                        rbReact[0],
                        rbReact[3],
                        rbReact[2],
                    )
                    self._energy_react = struct.unpack(">I", rbReact)[0]

                elif "power" in param.lower():
                    if len(payload) < 4:
                        print(f"Ошибка чтения {param} - ответ короткий")
                        continue

                    rbPower = (struct.unpack("<h", payload[2:4])[0] / 100) * 50

                    # Update the appropriate power property
                    power_mapping = {
                        "TotalPowerActive": "_pwr_act",
                        "PowerActiveL1": "_pwr_aL1",
                        "PowerActiveL2": "_pwr_aL2",
                        "PowerActiveL3": "_pwr_aL3",
                        "TotalPowerReactive": "_pwr_react",
                        "PowerReactiveL1": "_pwr_rL1",
                        "PowerReactiveL2": "_pwr_rL2",
                        "PowerReactiveL3": "_pwr_rL3",
                        "TotalPowerSeem": "_pwr_seem",
                        "PowerSeemL1": "_pwr_sL1",
                        "PowerSeemL2": "_pwr_sL2",
                        "PowerSeemL3": "_pwr_sL3",
                    }

                    if param in power_mapping:
                        setattr(
                            self,
                            power_mapping[param],
                            rbPower * (10 if param == "TotalPowerActive" else 1),
                        )

                elif "voltage" in param.lower():
                    if len(payload) < 4:
                        print(f"Ошибка чтения {param} - ответ короткий")
                        continue

                    rbVoltage = struct.unpack("<h", payload[2:4])[0] / 100

                    if param == "VoltageL1":
                        self._voltageL1 = rbVoltage
                    elif param == "VoltageL2":
                        self._voltageL2 = rbVoltage
                    elif param == "VoltageL3":
                        self._voltageL3 = rbVoltage

                elif "current" in param.lower():
                    if len(payload) < 4:
                        print(f"Ошибка чтения {param} - ответ короткий")
                        continue

                    rbCurrent = (struct.unpack("<h", payload[2:4])[0] / 1000) * 50

                    if param == "CurrentL1":
                        self._currentL1 = rbCurrent
                    elif param == "CurrentL2":
                        self._currentL2 = rbCurrent
                    elif param == "CurrentL3":
                        self._currentL3 = rbCurrent

                elif "cosf" in param.lower():
                    if len(payload) < 4:
                        print(f"Ошибка чтения cosf - ответ короткий")
                        continue

                    b = payload[1:4]
                    val = ((b[0] & 0x3F) << 16) | (b[2] << 8) | b[1]
                    self._cosf = val / 1000

            except Exception as e:
                print(f"Ошибка {param}: {str(e)}")
                continue


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Чтение параметров ПУ Э/Э Меркурий 236"
    )
    parser.add_argument(
        "--port",
        type=str,
        default="/dev/ttyUSB0",
        help="Серийный порт (default: /dev/ttyUSB0)",
    )
    parser.add_argument(
        "--baudrate", type=int, default=9600, help="Baud rate (default: 9600)"
    )
    parser.add_argument(
        "--parity",
        type=str,
        default="N",
        choices=["N", "E", "O"],
        help="Чётность (N-none, E-even, O-odd, default: N)",
    )
    parser.add_argument(
        "--bytesize",
        type=int,
        default=8,
        choices=[5, 6, 7, 8],
        help="Data bits (default: 8)",
    )
    parser.add_argument(
        "--stopbits", type=int, default=1, choices=[1, 2], help="Stop bits (default: 1)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Тайм-аут ожидания подключения в секундах (default: 1.0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        with EnergyMeter(
            port=args.port,
            baudrate=args.baudrate,
            parity=args.parity,
            bytesize=args.bytesize,
            stopbits=args.stopbits,
            timeout=args.timeout,
        ) as meter:
            meter.read_data()

            print("\nCurrent Measurements:")
            print(f"Active Energy: {meter.energy_act} Wh")
            print(f"Reactive Energy: {meter.energy_react} VARh")
            print(f"Active Power: {meter.pwr_act} W")
            print(f"Reactive Power: {meter.pwr_react} VAR")
            print(f"Apparent Power: {meter.pwr_seem} VA")
            print(
                f"Voltage L1: {meter.voltageL1} V, L2: {meter.voltageL2} V, L3: {meter.voltageL3} V"
            )
            print(
                f"Current L1: {meter.currentL1} A, L2: {meter.currentL2} A, L3: {meter.currentL3} A"
            )
            print(f"Frequency: {meter.freq} Hz")
            print(f"Power Factor: {meter.cosf}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

import time
from machine import I2C

class AS7343:
    def __init__(self, i2c, address=0x39):
        """
        初始化AS7343光谱传感器驱动类
        :param i2c: 已经初始化的machine.I2C对象
        :param address: 传感器固定I2C七位地址，默认为0x39
        """
        self.i2c = i2c
        self.address = address

    def write_register(self, reg, value):
        """向指定的8位寄存器地址写入单字节数据"""
        self.i2c.writeto_mem(self.address, reg, bytes([value]))

    def read_register(self, reg):
        """从指定的8位寄存器地址读取单字节数据"""
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def init_sensor(self):
        """
        按照芯片状态机要求，分步初始化配置AS7343传感器并开启18通道全扫描模式
        """
        self.write_register(0x80, 0x01)
        time.sleep_ms(2)

        self.write_register(0x81, 29)
        self.write_register(0xD4, 599 & 0xFF)
        self.write_register(0xD5, (599 >> 8) & 0xFF)

        self.write_register(0xD6, 0x60)
        self.write_register(0xC6, 0x07)
        self.write_register(0x80, 0x03)

    def is_data_ready(self):
        """
        检查当前周期的光谱转换是否已全量完成
        :return: 布尔值，True表示数据就绪可读
        """
        status2 = self.read_register(0x90)
        return (status2 & 0x40) != 0

    def read_all_channels(self):
        """
        利用I2C地址指针自增机制，批量读取36字节并解析全部通道数据
        :return: 包含各个通道实际ADC计数值的字典
        """
        data = self.i2c.readfrom_mem(self.address, 0x95, 36)
        raw_values = []
        for i in range(18):
            low_byte = data[i * 2]
            high_byte = data[i * 2 + 1]
            raw_values.append((high_byte << 8) | low_byte)
        
        spectral_data = {
            "FZ": raw_values[0],
            "FY": raw_values[1],
            "FXL": raw_values[2],
            "NIR": raw_values[3],
            "F2": raw_values[6],
            "F3": raw_values[7],
            "F4": raw_values[8],
            "F6": raw_values[9],
            "F1": raw_values[12],
            "F7": raw_values[13],
            "F8": raw_values[14],
            "F5": raw_values[15],
            "VIS": raw_values[4],
            "FD": raw_values[5]
        }
        return spectral_data

    def control_onboard_led(self, enable, current_ma=12):
        """
        控制AS7343传感器上自带的照明LED（通过LDR引脚恒流源驱动）
        :param enable: True开启LED，False关闭LED
        :param current_ma: 恒流驱动电流大小，单位mA（范围4mA至258mA，步进2mA）
        """
        if not enable:
            self.write_register(0xCD, 0x00)
            return

        if current_ma < 4:
            current_ma = 4
        elif current_ma > 258:
            current_ma = 258

        code = (current_ma - 4) // 2
        reg_value = 0x80 | (code & 0x7F)
        self.write_register(0xCD, reg_value)

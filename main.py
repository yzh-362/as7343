import time
from machine import Pin, I2C
import neopixel
from as7343 import AS7343

# 初始化WaveShare-RP2040-Zero板载WS2812 RGB LED（物理映射在引脚16，灯珠数量为1）
pixel_pin = Pin(16, Pin.OUT)
rgb_led = neopixel.NeoPixel(pixel_pin, 1)

def set_rgb_led(r, g, b):
    """设置RP2040板载可寻址RGB LED的颜色"""
    rgb_led[0] = (r, g, b)
    rgb_led.write()

# 初始化硬件I2C外设（GPIO 0 作为 SDA 线路，GPIO 1 作为 SCL 线路）
i2c_bus = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

# 实例化光谱传感器控制类
sensor = AS7343(i2c_bus)

# 设定内部全局变量用于记录板载LED闪烁状态
led_toggle_state = False

print("正在启动光谱数据采集监控程序...")

try:
    # 1. 硬件状态机配置与通道映射使能
    sensor.init_sensor()
    print("AS7343 光谱芯片配置成功。")

    # 2. 开启传感器自带的外部激发照明恒流LED（驱动电流配置为20mA）
    sensor.control_onboard_led(enable=True, current_ma=20)
    print("AS7343 板载照明源恒流器已开启。")

    # 3. 周期性数据检索及指示灯调度循环
    while True:
        # 通过逻辑值取反改变RP2040板载LED电平，提供绿光闪烁（Heartbeat）反馈
        if led_toggle_state:
            set_rgb_led(0, 64, 0)
        else:
            set_rgb_led(0, 0, 0)
        led_toggle_state = not led_toggle_state

        # 读取光谱传感器状态，若数据转换就绪则导出数值
        if sensor.is_data_ready():
            spectrum = sensor.read_all_channels()
            
            print("========================================")
            print("F1  (中心波长 400nm):", spectrum["F1"])
            print("F2  (中心波长 425nm):", spectrum["F2"])
            print("FZ  (中心波长 450nm):", spectrum["FZ"])
            print("F3  (中心波长 475nm):", spectrum["F3"])
            print("F4  (中心波长 515nm):", spectrum["F4"])
            print("FY  (中心波长 555nm):", spectrum["FY"])
            print("F5  (中心波长 550nm):", spectrum["F5"])
            print("FXL (中心波长 600nm):", spectrum["FXL"])
            print("F6  (中心波长 640nm):", spectrum["F6"])
            print("F7  (中心波长 690nm):", spectrum["F7"])
            print("F8  (中心波长 745nm):", spectrum["F8"])
            print("NIR (中心波长 855nm):", spectrum["NIR"])
            print("VIS (可见光全透):     ", spectrum["VIS"])
            print("FD  (闪烁检测通道):   ", spectrum["FD"])

        # 固定主循环步进延时500ms
        time.sleep_ms(500)

except Exception as error:
    print("运行时触发未知软件系统异常:", error)

finally:
    # 当用户发出终止指令或系统崩溃退出时，触发此清理块
    print("\n检测到退出指令，开始执行安全释放流...")
    
    # 1. 向 0xCD 寄存器写入 0x00，完全切断传感器硬件激发照明 LED 的驱动电流
    sensor.control_onboard_led(enable=False)
    
    # 2. 将控制树莓派板载可寻址灯珠的三个通道色彩缓存全数置零并清空显示
    set_rgb_led(0, 0, 0)
    
    print("系统清理完毕，两处物理LED光源已全自动安全关闭。")

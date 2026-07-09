import time
from machine import Pin, I2C
import neopixel
from as7343 import AS7343

# 1. 物理外设初始化
pixel_pin = Pin(16, Pin.OUT)
rgb_led = neopixel.NeoPixel(pixel_pin, 1)

def set_rgb_led(r, g, b):
    rgb_led[0] = (r, g, b)
    rgb_led.write()

i2c_bus = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
sensor = AS7343(i2c_bus)

# 2. 定义存储文件名
matrix_file = "reconstruction_matrix.csv"
raw_data_file = "raw_data.csv"
recon_data_file = "reconstructed_spectrum.csv"

# 3. 动态解析本地重建矩阵
reconstruction_matrix = []
matrix_channels = []
wavelengths = []

print("正在从物理文件系统读取重建矩阵...")
try:
    with open(matrix_file, "r") as f:
        # 读取第一行表头
        header = f.readline().strip().split(",")
        matrix_channels = header[1:]  # 提取对齐的通道名称顺序
        
        # 逐行解析波长与对应加权系数
        for line in f:
            parts = line.strip().split(",")
            if parts and len(parts) > 1:
                wavelengths.append(int(parts[0]))
                row_weights = [float(x) for x in parts[1:]]
                reconstruction_matrix.append(row_weights)
    print("重建矩阵配置成功加载，共计", len(wavelengths), "个波长节点。")
except Exception as e:
    print("矩阵加载异常，请确认 reconstruction_matrix.csv 已正确上载到根目录:", e)

# 4. 初始化创建输出 CSV 数据表格与表头
print("正在初始化 CSV 存储结构...")
with open(raw_data_file, "w") as f_raw:
    f_raw.write("Index,Timestamp_ms,F1,F2,FZ,F3,F4,FY,F5,FXL,F6,F7,F8,NIR,VIS,FD\n")

with open(recon_data_file, "w") as f_recon:
    # 动态生成包含具体纳米波长单位的 CSV 表头
    recon_header = "Index,Timestamp_ms," + ",".join([str(w) + "nm" for w in wavelengths]) + "\n"
    f_recon.write(recon_header)

# 全局运行变量
led_toggle_state = False
sample_index = 0

try:
    # 5. 传感器核心状态机激活
    sensor.init_sensor()
    sensor.control_onboard_led(enable=True, current_ma=20)
    print("系统初始化闭环构建完成，进入实时采集与重构流...")

    while True:
        # 板载状态指示灯动态翻转
        if led_toggle_state:
            set_rgb_led(0, 40, 0)
        else:
            set_rgb_led(0, 0, 0)
        led_toggle_state = not led_toggle_state

        # 检查光谱传感器数据是否转换就绪
        if sensor.is_data_ready():
            spectrum = sensor.read_all_channels()
            sample_index += 1
            current_time = time.ticks_ms()

            # A. 组装并追加存储原始通道数据
            raw_row = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                sample_index, current_time,
                spectrum["F1"], spectrum["F2"], spectrum["FZ"], spectrum["F3"],
                spectrum["F4"], spectrum["FY"], spectrum["F5"], spectrum["FXL"],
                spectrum["F6"], spectrum["F7"], spectrum["F8"], spectrum["NIR"],
                spectrum["VIS"], spectrum["FD"]
            )
            with open(raw_data_file, "a") as f_raw:
                f_raw.write(raw_row)

            # B. 执行实时光谱重建计算 (一维矩阵点乘与非负物理截断)
            # 严格按照从 CSV 读取到的通道顺序提取当前传感器的归一化数值值值
            X_input = [float(spectrum[ch]) for ch in matrix_channels]
            reconstructed_spectrum = []
            
            for row_weights in reconstruction_matrix:
                intensity = 0.0
                for j in range(len(X_input)):
                    intensity += row_weights[j] * X_input[j]
                # 物理非负约束
                if intensity < 0.0:
                    intensity = 0.0
                reconstructed_spectrum.append(intensity)

            # C. 组装并追加存储101维连续光谱数据
            recon_str_list = [f"{val:.4f}" for val in reconstructed_spectrum]
            recon_row = "{},{},{}\n".format(sample_index, current_time, ",".join(recon_str_list))
            with open(recon_data_file, "a") as f_recon:
                f_recon.write(recon_row)

            # D. 命令行终端调试输出
            print("========================================")
            print(f"样本序号: {sample_index} | 物理系统时间: {current_time} ms")
            print(f"原始特征值[FZ]: {spectrum['FZ']} | [FY]: {spectrum['FY']} | [NIR]: {spectrum['NIR']}")
            print(f"重建光谱端点 [380nm]: {reconstructed_spectrum[0]:.2f} | [880nm]: {reconstructed_spectrum[-1]:.2f}")
            print(f"状态: 数据成功同步写入至 {raw_data_file} 与 {recon_data_file}")

        time.sleep_ms(500)

except Exception as error:
    print("运行时触发未知系统异常:", error)

finally:
    print("\n检测到系统退出指令，开始释放硬件控制权...")
    sensor.control_onboard_led(enable=False)
    set_rgb_led(0, 0, 0)
    print("所有物理 LED 光源已安全关闭，文件已妥善保存于局部闪存。")
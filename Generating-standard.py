import numpy as np
import csv

# 1. 定义重建光谱的波长轴 (380nm 到 880nm，步进 5nm，共 101 个波长节点)
wavelengths = np.arange(380, 881, 5)
num_wavelengths = len(wavelengths)

# 2. 引入带有相对灵敏度物理修正的通道参数
# 注意：AS7343 各通道滤光片透过率与硅光电二极管在不同波长下的量子效率（QE）不同
# 此处引入的 peak_responsivity 修正因子用以模拟真实芯片的增益差异，比单纯高斯更符合物理实际
channel_params = [
    {"name": "F1",  "lambda_c": 405.0, "fwhm": 30.0, "peak_responsivity": 0.35},
    {"name": "F2",  "lambda_c": 425.0, "fwhm": 22.0, "peak_responsivity": 0.42},
    {"name": "FZ",  "lambda_c": 450.0, "fwhm": 55.0, "peak_responsivity": 0.85},
    {"name": "F3",  "lambda_c": 475.0, "fwhm": 30.0, "peak_responsivity": 0.48},
    {"name": "F4",  "lambda_c": 515.0, "fwhm": 40.0, "peak_responsivity": 0.55},
    {"name": "FY",  "lambda_c": 555.0, "fwhm": 100.0,"peak_responsivity": 0.95},
    {"name": "F5",  "lambda_c": 550.0, "fwhm": 35.0, "peak_responsivity": 0.60},
    {"name": "FXL", "lambda_c": 600.0, "fwhm": 80.0, "peak_responsivity": 0.75},
    {"name": "F6",  "lambda_c": 650.0, "fwhm": 55.0, "peak_responsivity": 0.65},
    {"name": "F7",  "lambda_c": 690.0, "fwhm": 55.0, "peak_responsivity": 0.58},
    {"name": "F8",  "lambda_c": 745.0, "fwhm": 60.0, "peak_responsivity": 0.50},
    {"name": "NIR", "lambda_c": 855.0, "fwhm": 54.0, "peak_responsivity": 0.40}
]
num_channels = len(channel_params)

# 3. 构造正向物理响应矩阵 R (维度: 12 行 x 101 列)
R = np.zeros((num_channels, num_wavelengths))
for i, param in enumerate(channel_params):
    l_c = param["lambda_c"]
    fwhm = param["fwhm"]
    resp = param["peak_responsivity"]
    # 基础响应曲线结合峰值响应增益
    R[i, :] = resp * np.exp(-4.0 * np.log(2.0) * ((wavelengths - l_c) ** 2) / (fwhm ** 2))

# 4. 计算反向重建矩阵 M (基于 Tikhonov 正则化)
# 将 alpha 适度调高（如 0.5），可以有效平滑求逆矩阵，减少端侧重建时由于噪声引起的数值剧烈跳变
alpha = 0.5
M = R.T @ np.linalg.inv(R @ R.T + alpha * np.eye(num_channels))

# 5. 将重建矩阵输出为规范的 CSV 表格
csv_filename = "reconstruction_matrix.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    header = ["Wavelength"] + [param["name"] for param in channel_params]
    writer.writerow(header)
    for idx, wl in enumerate(wavelengths):
        row = [int(wl)] + [float(val) for val in M[idx, :]]
        writer.writerow(row)

print(f"成功在当前目录下生成改良物理模型的重建矩阵文件: {csv_filename}")
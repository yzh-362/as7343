import numpy as np
import csv

# 1. 定义重建光谱的波长轴 (380nm 到 880nm，步进 5nm，共 101 个波长节点)
wavelengths = np.arange(380, 881, 5)
num_wavelengths = len(wavelengths)

# 2. 提取数据手册中固化的 12 个核心通道的中心波长与半高宽 (FWHM)
channel_params = [
    {"name": "F1",  "lambda_c": 405.0, "fwhm": 30.0},
    {"name": "F2",  "lambda_c": 425.0, "fwhm": 22.0},
    {"name": "FZ",  "lambda_c": 450.0, "fwhm": 55.0},
    {"name": "F3",  "lambda_c": 475.0, "fwhm": 30.0},
    {"name": "F4",  "lambda_c": 515.0, "fwhm": 40.0},
    {"name": "FY",  "lambda_c": 555.0, "fwhm": 100.0},
    {"name": "F5",  "lambda_c": 550.0, "fwhm": 35.0},
    {"name": "FXL", "lambda_c": 600.0, "fwhm": 80.0},
    {"name": "F6",  "lambda_c": 650.0, "fwhm": 55.0},
    {"name": "F7",  "lambda_c": 690.0, "fwhm": 55.0},
    {"name": "F8",  "lambda_c": 745.0, "fwhm": 60.0},
    {"name": "NIR", "lambda_c": 855.0, "fwhm": 54.0}
]
num_channels = len(channel_params)

# 3. 构造正向物理响应矩阵 R (维度: 12 行 x 101 列)
R = np.zeros((num_channels, num_wavelengths))
for i, param in enumerate(channel_params):
    l_c = param["lambda_c"]
    fwhm = param["fwhm"]
    R[i, :] = np.exp(-4.0 * np.log(2.0) * ((wavelengths - l_c) ** 2) / (fwhm ** 2))

# 4. 计算反向重建矩阵 M (维度: 101 行 x 12 列)
alpha = 0.01  # 正则化系数
M = R.T @ np.linalg.inv(R @ R.T + alpha * np.eye(num_channels))

# 5. 将重建矩阵输出为规范的 CSV 表格
csv_filename = "reconstruction_matrix.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # 写入表头，第一列为波长，后续列对应各个通道的加权系数
    header = ["Wavelength"] + [param["name"] for param in channel_params]
    writer.writerow(header)
    # 逐行写入 101 个波长节点的映射系数
    for idx, wl in enumerate(wavelengths):
        row = [int(wl)] + [float(val) for val in M[idx, :]]
        writer.writerow(row)

print(f"成功在当前目录下生成高斯拟合重建矩阵文件: {csv_filename}")
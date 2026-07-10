import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 读取 CSV 文件
df = pd.read_csv(r"D:\Documents\GitHub\as7343\reconstructed_spectrum.csv")

# 2. 提取纯光谱强度矩阵
wavelength_cols = [col for col in df.columns if "nm" in col]
spectrum_matrix = df[wavelength_cols]

# 3. 干净地提取波长和索引作为坐标轴标签
wavelengths = [col.replace("nm", "") for col in wavelength_cols]
sample_indices = df["Index"].values

# 4. 创建热力图画布
plt.figure(figsize=(12, 7), dpi=150)

# 5. 使用 seaborn 绘制热力图
# cmap='viridis' 或 'plasma' 能非常敏锐地捕捉到 0 值的断崖
sns.heatmap(
    spectrum_matrix, 
    xticklabels=wavelengths, 
    yticklabels=sample_indices, 
    cmap="viridis", 
    cbar_kws={'label': 'Intensity'}
)

# 6. 图表美化
plt.title("Spectral Intensity Distribution Heatmap", fontsize=14, fontweight='bold')
plt.xlabel("Wavelength (nm)", fontsize=12)
plt.ylabel("Sample Index", fontsize=12)

# 适当稀释 Y 轴标签防止重叠
plt.gca().set_yticks(plt.gca().get_yticks()[::max(1, len(sample_indices)//20)])

plt.tight_layout()
plt.savefig("spectrum_heatmap.png")
plt.show()
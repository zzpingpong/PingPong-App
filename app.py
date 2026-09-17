import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
import io

# --- 页面与中文字体配置 ---
st.set_page_config(page_title="乒乓球发球智能评估系统", layout="wide")
import os
from matplotlib import font_manager

# 动态加载当前目录下的中文字体文件
font_path = "simhei.ttf"
if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

st.title("🏓 乒乓球发球智能评估系统 (完整商业版)")
st.write("将数据转化为专业报告，只需三步。（提示：点击图片虚线框可直接 `Ctrl+V` 粘贴截图）")

# --- 第一部分：数据录入区 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 基础信息与 VAR 图像录入")
    player_name = st.text_input("请输入测试队员姓名：", value="测试队员")
    var_img = st.file_uploader("上传/粘贴 VAR 鹰眼合规截图", type=['jpg', 'png', 'jpeg'])
    
    col_a, col_b = st.columns(2)
    with col_a:
        angle = st.number_input("实测抛球角度 (°)", min_value=0.0, step=0.01, value=4.32)
    with col_b:
        height = st.number_input("实测抛球高度 (cm)", min_value=0.0, step=0.01, value=68.44)

with col2:
    st.subheader("2. 鹰眼 Excel 数据源录入")
    excel_file = st.file_uploader("上传 Excel 原始数据表 (.xlsx)", type=['xlsx', 'xls'])
    
    df = None
    if excel_file:
        df = pd.read_excel(excel_file)
        st.success("✅ 数据读取成功！已提取 速度、转速、过网高度 等核心指标。")
        st.dataframe(df.head(2)) # 仅预览前两行保持界面整洁

st.divider()

# --- 第二部分：核心计算与报告生成引擎 ---
def generate_pdf_report(name, angle, height, df_data, img_file):
    # 1. 数据计算
    avg_speed = df_data['速度'].mean()
    avg_spin = df_data['转速'].mean()
    avg_height = df_data['过网高度'].mean()
    avg_quality = df_data['旋转质量'].mean()
    
    total_serves = len(df_data)
    # 统计“是”的数量，计算上台率
    on_table = df_data['是否上台'].astype(str).str.contains('是').sum()
    passed = df_data['是否达标'].astype(str).str.contains('是').sum()
    on_table_rate = int((on_table / total_serves) * 100) if total_serves > 0 else 0
    
    # 2. 在内存中创建 PDF
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        # ===== PDF 第一页：合规性预警 =====
        fig1 = plt.figure(figsize=(8.27, 11.69), dpi=300) 
        fig1.text(0.5, 0.92, f"{name} 發球測試評估報告", ha='center', va='center', fontsize=24, fontweight='bold')
        fig1.text(0.1, 0.85, "一、 發球動作合規性預警", ha='left', va='center', fontsize=16, fontweight='bold')
        
        # 插入 VAR 截图
        if img_file:
            ax_img1 = fig1.add_axes([0.05, 0.55, 0.9, 0.28])
            ax_img1.imshow(Image.open(img_file))
            ax_img1.axis('off')
            
        # 智能诊断话术
        h_status = "合格" if height >= 16 else "違例"
        a_status = "完全合格" if angle <= 30 else "觸發違例警告"
        
        text1 = (
            f"拋球高度： {height} cm。國際乒聯規定需大於 16 cm，此項 {h_status}。\n\n"
            f"拋球角度： {angle}°。嚴格對照「小於等於 30°」的合法紅線標準，此項 {a_status}。\n"
            f"系統診斷： 該隊員的拋球動作{'在合法範圍內，基本功紮實規範，無犯規隱患' if angle <= 30 else '存在明顯的斜拋借力習慣，實戰中極易被判罰失分，需立即糾正'}。"
        )
        fig1.text(0.1, 0.45, text1, ha='left', va='top', fontsize=12, linespacing=2)
        pdf.savefig(fig1)
        plt.close(fig1)
        
        # ===== PDF 第二页：雷达图、柱状图与质量总评 =====
        fig2 = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig2.text(0.1, 0.92, "二、 發球質量與穩定性分析", ha='left', va='center', fontsize=16, fontweight='bold')
        
        # 绘制雷达图
        ax_radar = fig2.add_axes([0.1, 0.55, 0.35, 0.3], polar=True)
        metrics = {'平均轉速 (r/s)': avg_spin, '平均速度 (km/h)': avg_speed, '過網高度 (cm)': avg_height, '旋轉質量': avg_quality}
        labels = np.array(list(metrics.keys()))
        stats = np.array(list(metrics.values()))
        angles_arr = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
        stats = np.concatenate((stats, [stats[0]]))
        angles_arr = np.concatenate((angles_arr, [angles_arr[0]]))
        
        ax_radar.fill(angles_arr, stats, color='#7CB5EC', alpha=0.5)
        ax_radar.plot(angles_arr, stats, color='#00529B', linewidth=2)
        ax_radar.set_xticks(angles_arr[:-1])
        ax_radar.set_xticklabels(labels, fontsize=10)
        ax_radar.set_yticks([10, 20, 30, 40, 50]) # 加上单位刻度！
        ax_radar.set_yticklabels(['10', '20', '30', '40', '50'], color="grey", size=8)
        ax_radar.set_title("發球核心威脅性指標", pad=20)
        
        # 绘制稳定性柱状图
        ax_bar = fig2.add_axes([0.55, 0.55, 0.35, 0.3])
        ax_bar.bar(['總發球數', '上台數', '達標數'], [total_serves, on_table, passed], color=['#D3D3D3', '#2CA02C', '#FF7F0E'], width=0.5)
        ax_bar.set_ylim(0, total_serves + 2)
        ax_bar.set_title(f"發球穩定性 (上台率: {on_table_rate}%)", pad=20)
        # 柱状图上加数字
        for i, v in enumerate([total_serves, on_table, passed]):
            ax_bar.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

        # 智能总评话术
        text2 = (
            f"質量總評：\n"
            f"該隊員穩定性表現為上台率 {on_table_rate}%。從雷達圖數據可見，其平均轉速達到了 {avg_spin:.2f} r/s，\n"
            f"平均速度為 {avg_speed:.2f} km/h。整體發球展現出了{'極佳的威脅性與穩定性' if on_table_rate >= 80 else '一定的起伏，仍需強化手感'}。\n\n"
            f"訓練改進建議：\n"
            f"1. {'固化動力鏈： 目前拋球角度與發力配合極佳，請將此動作形成深度肌肉記憶。' if angle <= 30 else '重構發力軸： 必須立刻停止斜拋借力，在垂直拋球的基礎上重新找尋擊球節奏。'}\n"
            f"2. {'強化落點欺騙性： 建議在現有高質量基礎上，加入更多長短球與旋轉反差變化。' if on_table_rate >= 80 else '提升上台率： 暫時降低發力極限，優先保證過網弧線與第一落點的安全系數。'}"
        )
        fig2.text(0.1, 0.40, text2, ha='left', va='top', fontsize=12, linespacing=1.8)
        pdf.savefig(fig2)
        plt.close(fig2)
        
    return pdf_buffer

# --- 按钮与执行区 ---
if st.button("🚀 智能分析並生成 PDF 報告", use_container_width=True):
    if not var_img or df is None:
        st.warning("⚠️ 報告生成失敗：請確保【VAR 截圖】與【Excel 數據表】均已上傳！")
    else:
        with st.spinner("系統正在進行運動學運算與報告排版，請稍候..."):
            pdf_data = generate_pdf_report(player_name, angle, height, df, var_img)
            
            st.success("✅ 報告生成完畢！雷達圖單位與刻度已補齊，排版標準完全對標專業版。")
            
            # 提供直接下载按钮
            st.download_button(
                label="📥 點擊下載高清 PDF 報告",
                data=pdf_data.getvalue(),
                file_name=f"{player_name}_發球測試評估報告.pdf",
                mime="application/pdf",
                type="primary"
            )

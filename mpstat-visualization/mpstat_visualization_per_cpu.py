import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import re

# ----------------- 設定 -----------------
FILE_PATH = 'mpstat-test.log' # mpstatの出力ファイル名
# ----------------------------------------

def visualize_mpstat_overlay(file_path):
    """
    mpstatの出力を読み込み、個別のCPUコアの利用率を一つのグラフに重ねて可視化する。
    Timestampのオーバーフローを防ぐため、時刻文字列をX軸に使う。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return

    # データの抽出と整形
    lines = []
    header_match = re.search(r'CPU\s+%usr\s+%nice', data)

    if not header_match:
        print("エラー: mpstatのデータ形式を認識できませんでした。")
        return

    data_start_index = header_match.end()
    data_lines = data[data_start_index:].split('\n')

    for line in data_lines:
        #if re.match(r'^\d{2}:\d{2}:\d{2}\s+(all|\d+)', line.strip()):
        if re.match(r'^\d{1,2}:\d{2}:\d{2}\s+(AM|PM)\s+(all|\d+)', line.strip()):
            lines.append(line.strip())

    # AM/PM を削除（正規表現で対応）
    lines = [re.sub(r"\s+(AM|PM)\b", "", line) for line in lines]

    # ヘッダーを付与してDataFrameとして読み込み
    mpstat_header = "Time CPU %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle"
    csv_data = "\n".join([mpstat_header] + lines)

    df = pd.read_csv(
        StringIO(csv_data),
        sep=r'\s+',
        engine='python'
    )

    # 可視化のための総利用率 (Total_Used) を計算
    df['Total_Used'] = 100.0 - df['%idle']

    # 'all' (全体) のデータは除外し、個別のCPUコア（数値）のデータのみを抽出
    df_cpu_cores = df[df['CPU'] != 'all'].copy()

    # グラフの作成
    fig, ax = plt.subplots(figsize=(14, 8)) # axオブジェクトを取得

    # 各CPUコアに対してループ処理を行い、Total_Usedをプロット
    cpu_cores = sorted(df_cpu_cores['CPU'].unique())

    # X軸の時刻ラベルを取得（重複を避けるためユニークなものを利用）
    time_labels = df_cpu_cores['Time'].unique()

    for cpu in cpu_cores:
        df_plot = df_cpu_cores[df_cpu_cores['CPU'] == cpu]

        # ------------------- 💡 修正箇所 💡 -------------------
        # matplotlib.pyplot.plot を直接使用し、X軸に時刻文字列 (Time) を渡す
        ax.plot(
            df_plot['Time'],  # X軸: 時刻文字列 ('17:17:15')
            df_plot['Total_Used'], # Y軸: 数値
            label=f'CPU {cpu}',
            linewidth=2,
            marker='o', markersize=4
        )
        # --------------------------------------------------------

    # タイトルとラベル
    ax.set_title('CPU Core Utilization Trends (Overlay)', fontsize=16)
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Total CPU Used (%)', fontsize=12)

    # Y軸の範囲を0から100に固定
    ax.set_ylim(0, 100)

    # X軸の目盛りを設定し、回転させる
    ax.set_xticks(time_labels)
    plt.xticks(rotation=45, ha='right')

    # 凡例の設定
    ax.legend(title='CPU Core', loc='upper left', bbox_to_anchor=(1.05, 1))

    ax.grid(axis='both', linestyle='--', alpha=0.7)

    # tight_layoutの呼び出しを維持
    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

# スクリプトの実行
visualize_mpstat_overlay(FILE_PATH)

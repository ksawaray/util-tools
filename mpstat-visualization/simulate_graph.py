import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ----------------- シミュレーション設定 -----------------
NUM_CORES = 32      # CPUコアの数 (0から31)
TIME_POINTS = 60    # 測定時間 (60秒間)
# --------------------------------------------------------

def simulate_and_visualize_high_core_count():
    """
    32個のCPUコアの利用率データをシミュレーションし、単一グラフに重ねてプロットする。
    ダミー日付をエポックに近い日付 (1970-01-01) に設定し、OverflowErrorを回避する。
    """

    # 時刻データの生成
    # 💡 修正点: start='1970-01-01 09:00:00' に変更
    # Unix Epochに近い日付に設定することで、内部的な整数値のオーバーフローを防ぐ
    times = pd.date_range('1970-01-01 09:00:00', periods=TIME_POINTS, freq='1S') 

    # データを格納するDataFrameを初期化
    data = {}

    # 32コア分の利用率を生成
    for i in range(NUM_CORES):
        # 1. 基本的なバックグラウンドノイズ (0-10%)
        utilization = np.random.uniform(0, 10, size=TIME_POINTS)

        # 2. コア0, 1, 2, 3 にはランダムなスパイクを追加 (10-40%)
        if i in [0, 1, 2, 3]:
            spike_intensity = np.random.uniform(10, 40, size=TIME_POINTS)
            utilization += spike_intensity * np.random.rand(TIME_POINTS)

        # 3. コア31 には永続的な高負荷を追加 (50-80%)
        if i == 31:
            utilization += np.random.uniform(50, 80, size=TIME_POINTS)

        utilization = np.clip(utilization, 0, 100)

        data[f'CPU {i}'] = utilization

    # インデックスにフルタイムスタンプ (datetime.datetime) を設定
    df = pd.DataFrame(data, index=times)

    # グラフの作成
    fig, ax = plt.subplots(figsize=(14, 8))

    # すべての線をプロット
    # pandasはdatetime.datetimeインデックスを自動的に時間軸として処理する
    df.plot(ax=ax, linewidth=1)

    # タイトルとラベル
    ax.set_title(f'CPU Utilization: {NUM_CORES} Cores Overlaid (Simulation)', fontsize=16)
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Total CPU Used (%)', fontsize=12)

    # Y軸の範囲を0から100に固定
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # X軸の表示形式を時刻のみにする
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))

    # 凡例をグラフの外に配置
    ax.legend(title='CPU Core', loc='upper left', bbox_to_anchor=(1.05, 1), ncol=1, fontsize=8)

    plt.tight_layout()
    plt.show()

# スクリプトの実行
simulate_and_visualize_high_core_count()

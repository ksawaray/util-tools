import argparse
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import re

def visualize_mpstat(file_path):
    """
    mpstatの出力を読み込み、CPU利用率を時系列で可視化する。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return

    # 必要な行（時刻と統計情報を含む行）のみを抽出
    # 統計情報の行は数値で始まり、特定の列を持つ
    lines = []
    header_found = False

    # mpstatのヘッダー行を検索
    header_match = re.search(r'CPU\s+%usr\s+%nice', data)
    if header_match:
        # ヘッダーの次の行から実際のデータを抽出
        data_start_index = header_match.end()
        data_lines = data[data_start_index:].split('\n')

        for line in data_lines:
            # 時刻と 'all' または 'CPU番号' を含む行を抽出（不要な空行や平均行を除く）
            #if re.match(r'^\d{2}:\d{2}:\d{2}\s+(all|\d+)', line.strip()):
            if re.match(r'^\d{1,2}:\d{2}:\d{2}\s+(AM|PM)\s+(all|\d+)', line.strip()):
                lines.append(line.strip())
                header_found = True

    # AM/PM を削除（正規表現で対応）
    lines = [re.sub(r"\s+(AM|PM)\b", "", line) for line in lines]

    if not header_found:
        print("エラー: mpstatのデータ形式を認識できませんでした。")
        return

    # データを文字列として結合し、StringIOでPandasに読み込ませる準備
    # mpstatの出力にはヘッダー行がデータ行と分離されているため、手動でヘッダーを付与
    mpstat_header = "Time CPU %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle"

    # データをCSV形式の文字列として再構築
    csv_data = "\n".join([mpstat_header] + lines)

    # StringIOを使ってDataFrameとして読み込み
    df = pd.read_csv(
        StringIO(csv_data),
        sep=r'\s+', # スペース区切り
        engine='python' # 正規表現を使用するため
    )

    # Time列をdatetime型に変換
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time

    # 全CPU ('all') のデータのみを抽出
    df_all = df[df['CPU'] == 'all'].copy()

    # 可視化に必要な列を選択
    # グラフのX軸として使用するために、Time列をインデックスに設定
    df_plot = df_all.set_index('Time')[['%usr', '%sys', '%iowait', '%idle']]

    # グラフの作成
    plt.figure(figsize=(12, 6))

    # 積み重ねた折れ線グラフ（エリアプロット）で利用率を表現
    # %idleはプロットせず、他の利用率(%usr, %sys, %iowait)の合計を可視化
    df_plot[['%usr', '%sys', '%iowait']].plot(
        kind='area',
        stacked=True,
        ax=plt.gca(),
        linewidth=0.5,
        alpha=0.8
    )

    # タイトルとラベル
    plt.title('CPU Utilization Over Time (Overall)', fontsize=16)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('CPU Utilization (%)', fontsize=12)

    # Y軸の範囲を0から100に固定
    plt.ylim(0, 100)

    # グリッド表示
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 凡例の設定
    plt.legend(title='Metrics', loc='upper right')

    plt.tight_layout()
    plt.show()

# 引数からファイル名の取得
parser = argparse.ArgumentParser(
    description="mpstatログから種別ごとのCPU使用率を時間軸で可視化"
)
parser.add_argument("-f", "--file", required=True, help="mpstatの入力ファイルパス")
args = parser.parse_args()
# スクリプトの実行
visualize_mpstat(args.file)

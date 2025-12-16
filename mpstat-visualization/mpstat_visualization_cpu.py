import re
import argparse
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---- 正規表現：AM/PM付きのmpstatデータ行を抽出 ----
# 例:
# 11:38:09 AM  all    2.76    0.00    1.07    0.00    0.00    0.19    0.00    0.00    0.00   95.99
# 11:38:09 AM    1    4.95    0.00   22.77    0.00    0.00    1.98    0.00    0.00    0.00   70.30
ROW_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<time>\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM))    # 時刻(AM/PM付)
    \s+
    (?P<cpu>all|\d+)                             # CPU番号 or 'all'
    \s+
    (?P<usr>[-+]?\d+(?:\.\d+)?)                  # %usr
    \s+
    (?P<nice>[-+]?\d+(?:\.\d+)?)                 # %nice
    \s+
    (?P<sys>[-+]?\d+(?:\.\d+)?)                  # %sys
    \s+
    (?P<iowait>[-+]?\d+(?:\.\d+)?)               # %iowait
    \s+
    (?P<irq>[-+]?\d+(?:\.\d+)?)                  # %irq
    \s+
    (?P<soft>[-+]?\d+(?:\.\d+)?)                 # %soft
    \s+
    (?P<steal>[-+]?\d+(?:\.\d+)?)                # %steal
    \s+
    (?P<guest>[-+]?\d+(?:\.\d+)?)                # %guest
    \s+
    (?P<gnice>[-+]?\d+(?:\.\d+)?)                # %gnice
    \s+
    (?P<idle>[-+]?\d+(?:\.\d+)?)                 # %idle
    \s*$
    """,
    re.VERBOSE
)

METRIC_MAP = {
    "%usr": "usr",
    "%nice": "nice",
    "%sys": "sys",
    "%iowait": "iowait",
    "%irq": "irq",
    "%soft": "soft",
    "%steal": "steal",
    "%guest": "guest",
    "%gnice": "gnice",
    "%idle": "idle",
}

def parse_mpstat_lines(text: str) -> pd.DataFrame:
    """mpstatのテキストからデータ行のみ抽出し、DataFrameを返す。"""
    rows: List[Dict] = []
    for line in text.splitlines():
        m = ROW_PATTERN.match(line)
        if not m:
            continue
        g = m.groupdict()
        rows.append({
            "Time": g["time"],      # '11:38:09 AM'
            "CPU": g["cpu"],        # 'all' or '0','1',...
            "%usr": float(g["usr"]),
            "%nice": float(g["nice"]),
            "%sys": float(g["sys"]),
            "%iowait": float(g["iowait"]),
            "%irq": float(g["irq"]),
            "%soft": float(g["soft"]),
            "%steal": float(g["steal"]),
            "%guest": float(g["guest"]),
            "%gnice": float(g["gnice"]),
            "%idle": float(g["idle"]),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("mpstatのデータ行を抽出できませんでした。正規表現とログ形式を確認してください。")
    return df

def plot_cpu_metrics(df: pd.DataFrame, cpu_id: str, metrics: List[str], out_path: str = None):
    """指定CPUについて、時間を横軸に各メトリクスを重ね描画。"""
    # CPU列は文字列に統一、'all'は除外
    df["CPU"] = df["CPU"].astype(str)
    df = df[df["CPU"] != "all"].copy()

    # 対象CPUの抽出
    target = df[df["CPU"] == str(cpu_id)].copy()
    if target.empty:
        raise ValueError(f"CPU {cpu_id} のデータがありません。CPU番号やログを確認してください。")

    # 時刻をdatetimeへ（AM/PM形式）
    target["TimeDT"] = pd.to_datetime(target["Time"], format="%I:%M:%S %p", errors="coerce")
    target = target.dropna(subset=["TimeDT"])
    if target.empty:
        raise ValueError("時刻の変換に失敗しました（AM/PM形式か要確認）。")

    # プロット準備
    plt.figure(figsize=(14, 8))
    ax = plt.gca()

    # メトリクスの正規化（'%usr' → 'usr' キー名へ）
    metrics_keys = []
    for m in metrics:
        if m not in METRIC_MAP:
            raise ValueError(f"未知のメトリクス: {m}. 利用可能: {', '.join(METRIC_MAP.keys())}")
        metrics_keys.append(METRIC_MAP[m])

    # 各メトリクスを描画
    for m_label, m_key in zip(metrics, metrics_keys):
        y = target[m_label]  # DataFrame列は'%usr'などラベルのまま保持
        ax.plot(
            target["TimeDT"],
            y,
            label=m_label, linewidth=2, marker="o", markersize=4
        )

    # 軸・凡例・グリッド
    ax.set_title(f"Changes in CPU{cpu_id} Usage ({', '.join(metrics)})", fontsize=16)
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("CPU Usage (%)", fontsize=12)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%I:%M:%S %p"))  # 例: 11:38:09 AM
    plt.xticks(rotation=45, ha="right")
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(title="Metrics", loc="upper left", bbox_to_anchor=(1.05, 1))
    ax.grid(axis="both", linestyle="--", alpha=0.7)
    plt.tight_layout(rect=[0, 0, 0.9, 1])

    if out_path:
        plt.savefig(out_path, dpi=150)
        print(f"[info] 画像を保存しました: {out_path}")
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(
        description="mpstatログから特定CPUの各使用率を時間軸で可視化"
    )
    parser.add_argument("-f", "--file", required=True, help="mpstat出力ファイルパス")
    parser.add_argument("-c", "--cpu", required=True, help="対象CPU番号（例: 0, 1, ...）")
    parser.add_argument(
        "-m", "--metrics",
        default="%usr,%nice,%sys,%iowait",
        help="表示メトリクス（カンマ区切り）。例: %usr,%nice,%sys,%iowait,%irq,%soft,%steal,%guest,%gnice,%idle"
    )
    parser.add_argument("-o", "--out", default=None, help="画像の保存先（PNG）。未指定なら表示")
    args = parser.parse_args()

    # ファイル読み込み
    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    df = parse_mpstat_lines(text)
    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    plot_cpu_metrics(df, args.cpu, metrics, out_path=args.out)

if __name__ == "__main__":
    main()


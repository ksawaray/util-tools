import re
import argparse
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---- 正規表現：AM/PM付きのsar -n DEVデータ行を抽出 ----
# 例:
# 12:00:16 AM     IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
# 12:10:07 AM        lo      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
# 12:10:07 AM   ens22f0      1.12      0.02      0.15      0.00      0.00      0.00      1.02      0.00
ROW_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<time>\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM))    # 時刻(AM/PM付)
    \s+
    (?P<iface>\S+)                               # インタフェース名 or 'IFACE'
    \s+
    (?P<rxpck>[-+]?\d+(?:\.\d+)?)                # rxpck/s
    \s+
    (?P<txpck>[-+]?\d+(?:\.\d+)?)                # txpck/s
    \s+
    (?P<rxkb>[-+]?\d+(?:\.\d+)?)                 # rxkB/s
    \s+
    (?P<txkb>[-+]?\d+(?:\.\d+)?)                 # txkB/s
    \s+
    (?P<rxcmp>[-+]?\d+(?:\.\d+)?)                # rxcmp/s
    \s+
    (?P<txcmp>[-+]?\d+(?:\.\d+)?)                # txcmp/s
    \s+
    (?P<rxmcst>[-+]?\d+(?:\.\d+)?)               # rxmcst/s
    \s+
    (?P<ifutil>[-+]?\d+(?:\.\d+)?)               # %ifutil
    \s*$
    """,
    re.VERBOSE
)

METRIC_MAP = {
    "rxpck/s": "rxpck",
    "txpck/s": "txpck",
    "rxkb/s": "rxkb",
    "txkb/s": "txkb",
    "rxcmp/s": "rxcmp",
    "txcmp/s": "txcmp",
    "rxmcst/s": "rxmcst",
    "%ifutil": "ifutil",
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
            "iface": g["iface"],        # インタフェース名
            "rxpck/s": float(g["rxpck"]),
            "txpck/s": float(g["txpck"]),
            "rxkb/s": float(g["rxkb"]),
            "txkb/s": float(g["txkb"]),
            "rxcmp/s": float(g["rxcmp"]),
            "txcmp/s": float(g["txcmp"]),
            "rxmcst/s": float(g["rxmcst"]),
            "%ifutil": float(g["ifutil"]),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("mpstatのデータ行を抽出できませんでした。正規表現とログ形式を確認してください。")
    return df

def plot_cpu_metrics(df: pd.DataFrame, iface: str, metrics: List[str], out_path: str = None):
    """指定CPUについて、時間を横軸に各メトリクスを重ね描画。"""
    # IFACE列は文字列に統一、'IFACE'は除外
    df["iface"] = df["iface"].astype(str)
    #df = df[df["iface"] != "IFACE"].copy()

    # 対象IFACEの抽出
    target = df[df["iface"] == str(iface)].copy()
    if target.empty:
        raise ValueError(f"IFACE {iface} のデータがありません。IFACEを確認してください。")

    # 時刻をdatetimeへ（AM/PM形式）
    target["TimeDT"] = pd.to_datetime(target["Time"], format="%I:%M:%S %p", errors="coerce")
    target = target.dropna(subset=["TimeDT"])
    if target.empty:
        raise ValueError("時刻の変換に失敗しました（AM/PM形式か要確認）。")

    # プロット準備
    plt.figure(figsize=(14, 8))
    ax = plt.gca()
    ax2 = ax.twinx()

    # メトリクスの正規化（'%ifutil' → 'ifutil' キー名へ）
    metrics_keys = []
    for m in metrics:
        if m not in METRIC_MAP:
            raise ValueError(f"未知のメトリクス: {m}. 利用可能: {', '.join(METRIC_MAP.keys())}")
        metrics_keys.append(METRIC_MAP[m])

    # 各メトリクスを描画
    for m_label, m_key in zip(metrics, metrics_keys):
        y = target[m_label]
        if m_label == "%ifutil":
            # ifutil は右軸に描画
            ax2.plot(target["TimeDT"], y, label=m_label,
                linewidth=2, marker="o", markersize=4, color="red")
        else:
            # その他は左軸に描画
            ax.plot(target["TimeDT"], y, label=m_label,
                linewidth=2, marker="o", markersize=4)

    # 軸・凡例・グリッド
    ax.set_title(f"Network Info Changes in {iface} ({', '.join(metrics)})", fontsize=16)
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Packets/KB/s etc.", fontsize=12)
    ax2.set_ylabel("%ifutil", fontsize=12)
    ax2.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%I:%M:%S %p"))  # 例: 11:38:09 AM
    plt.xticks(rotation=45, ha="right")
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    if handles1 and handles2:
        plt.legend(handles1 + handles2, labels1 + labels2,
           title="Metrics", loc="upper left", bbox_to_anchor=(1.05, 1))
    ax.grid(axis="both", linestyle="--", alpha=0.7)
    plt.tight_layout(rect=[0, 0, 0.9, 1])

    if out_path:
        plt.savefig(out_path, dpi=150)
        print(f"[info] 画像を保存しました: {out_path}")
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(
        description="sar -n DEVログから特定インタフェースのネットワーク情報を時間軸で可視化"
    )
    parser.add_argument("-f", "--file", required=True, help="sar出力ファイルパス")
    parser.add_argument("-i", "--iface", required=True, help="対象IFACE名 例: eno1)")
    parser.add_argument(
        "-m", "--metrics",
        default="rxpck/s,txpck/s,rxkb/s,txkb/s,rxcmp/s,txcmp/s,rxmcst/s,%ifutil",
        help="表示メトリクス（カンマ区切り）。例: rxpck/s,txpck/s,rxkb/s,txkb/s,rxcmp/s,txcmp/s,rxmcst/s,%ifutil"
    )
    parser.add_argument("-o", "--out", default=None, help="画像の保存先 (PNG)。未指定なら表示")
    args = parser.parse_args()

    # ファイル読み込み
    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    df = parse_mpstat_lines(text)
    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    plot_cpu_metrics(df, args.iface, metrics, out_path=args.out)

if __name__ == "__main__":
    main()

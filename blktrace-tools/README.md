# blktrace-tools

calc_diff_events.py: blktrace の結果から特定の 2 つのイベントの発行時刻の差分を計算するプログラム

## Environment

- Python 3.11.7
- Libraries
    - pandas 2.2.2

## How to use

`blktrace` によりイベントの情報を取得する。

```bash
# ファイルへの書き込みが終わったら Ctrl+C で止める
$ date; blktrace <デバイス名>
```

ファイル書き込みの例

```bash
$ date; taskset -c 1 dd if=/dev/zero of=test bs=1024k count=15000
```

`blkparse` により特定のイベントを抽出する。

```bash
$ blkparse <デバイス名> -a issue -f "%T.%t,%S,%N,%C\n" -q -o issue.csv
$ blkparse <デバイス名> -a complete -f "%T.%t,%S,%N,%C\n" -q -o complete.csv
```

スクリプトを実行する。

```bash
$ python calc_diff_events.py issue.csv complete.csv -o diff.csv
```


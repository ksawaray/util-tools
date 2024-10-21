# update-aws-sg

aws sg に自宅などの特定の IP アドレスからのみアクセスできるようにしている場合において、IP アドレスの更新を sg に反映させるスクリプト。  

## How to use

1. スクリプトの先頭にある `MYSECGROUP` に対象 SG の ARN をセットする
1. スクリプトを実行する

```bash
./update_aws_sg.sh
```


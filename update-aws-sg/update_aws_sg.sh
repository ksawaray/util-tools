#!/bin/bash

# 対象の sg arn
MYSECGROUP=sg-xxxxxxxxxxxxxxxxx
MYIP=$(curl -s http://checkip.amazonaws.com/)

echo "current ip address: $MYIP"
if [ -e myip.txt ]; then
	PREIP=$(<myip.txt)
	if [ $PREIP == $MYIP ]; then
		echo "not change ip address."
		exit 0
	fi
	echo "not equal current ip address and pre ip address. $PREIP (pre ip) is not $MYIP (current ip)."
  # アドレスが変わっているため、設定していたアドレスを sg から除外する
	aws --profile root ec2 revoke-security-group-ingress --group-id $MYSECGROUP --protocol tcp --port 22 --cidr $MYIP/32
	rm ./myip.txt
else
        echo "not found ./myip.txt. So, create file named myip.txt."
fi

# 現在のアドレスを myip.txt に書き込む
curl -s -o ./myip.txt http://checkip.amazonaws.com/
# 現在の新しいアドレスを sg に設定する
aws --profile root ec2 authorize-security-group-ingress --group-id $MYSECGROUP --protocol tcp --port 22 --cidr $MYIP/32


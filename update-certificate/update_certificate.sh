#!/bin/bash

# get remain days
remain_days=$(certbot certificates -d prompt-guesser.marginext.net|grep -oE "[0-9]+ days"|awk -F" " '{print $1}')

if [ "$remain_days" -lt 45 ]; then
        echo "start updating the certificate."
        systemctl stop nginx
        sleep 5
        certbot renew
        sleep 5
        systemctl start nginx
        echo "finish updating the certificate."
else
        echo "There is no need to renew the certificate."
        exit 0
fi

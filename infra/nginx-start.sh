#!/bin/sh
# Cloud Run の PORT 環境変数に合わせて Nginx のポートを動的に変更

PORT=${PORT:-8080}

# nginx.conf テンプレートの listen ポートを環境変数 PORT に置換
sed "s/listen 8080;/listen ${PORT};/" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Nginx を起動
exec nginx -g 'daemon off;'


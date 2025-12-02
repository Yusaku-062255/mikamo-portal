FROM node:20-alpine

WORKDIR /app

# 依存関係のインストール
COPY package.json package-lock.json* ./
RUN npm install

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 5173

# 開発サーバー起動
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


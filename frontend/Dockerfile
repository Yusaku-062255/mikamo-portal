FROM node:20-alpine

WORKDIR /app

# 依存関係のインストール
COPY package.json package-lock.json* ./
RUN npm install

# アプリケーションコードのコピー（.env.productionも含む）
COPY . .

# 本番ビルド（.env.productionが自動で読み込まれる）
RUN npm run build

# ポート公開
EXPOSE 5173

# プレビューサーバー起動（ビルド済みファイルを配信）
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]

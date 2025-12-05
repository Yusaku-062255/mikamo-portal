/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // テナント設定可能なプライマリカラー（CSS変数経由）
        'primary': 'var(--color-primary, #1e40af)',
        'primary-hover': 'var(--color-primary-hover, #1d4ed8)',
        // レガシー互換（将来削除予定）
        'mikamo-blue': 'var(--color-primary, #1e40af)',
        'mikamo-orange': '#f97316',
      },
    },
  },
  plugins: [],
}


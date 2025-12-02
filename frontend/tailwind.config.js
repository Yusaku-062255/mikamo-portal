/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mikamo-blue': '#1e40af',
        'mikamo-orange': '#f97316',
      },
    },
  },
  plugins: [],
}


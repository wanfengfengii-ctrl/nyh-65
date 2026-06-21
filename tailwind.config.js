/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        ceramic: {
          celadon: '#5D8A66',
          clay: '#8B6914',
          paper: '#F5F0E8',
          rice: '#FAF6ED',
          border: '#E8DFC9',
          ink: '#5D4E2B',
        }
      },
      fontFamily: {
        serif: ['"Source Han Serif SC"', '"Noto Serif SC"', 'SimSun', 'serif'],
        sans: ['"Source Han Sans SC"', '"Noto Sans SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

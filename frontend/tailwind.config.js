/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#101828',
        paper: '#f7f8f5',
        brand: { 50: '#ecfdf8', 100: '#d1faef', 500: '#12a880', 600: '#0a8567', 700: '#076a55' },
      },
      boxShadow: { card: '0 12px 32px rgba(16, 24, 40, 0.08)' },
    },
  },
  plugins: [],
}

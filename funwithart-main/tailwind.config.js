/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          cream: "#F5F0E6",
          clay: "#A47148",
          terracotta: "#D8A47F",
          charcoal: "#2E2E2E",
          sage: "#A3B18A",
          blush: "#E5B1A1",
          lavender: "#B8B8D1",
        }
      },
      fontFamily: {
        playfair: ["'Playfair Display'", "serif"],
        inter: ["Inter", "sans-serif"],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.8s ease-out forwards',
        'fade-in': 'fadeIn 1s ease-out forwards',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      }
    },
  },
  plugins: [],
}

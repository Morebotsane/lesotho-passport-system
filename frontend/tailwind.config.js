/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Lesotho flag colors 🇱🇸
        lesotho: {
          blue: '#00209F',
          green: '#009543',
          white: '#FFFFFF',
        },
        // Primary color scale (Blue - for main actions)
        primary: {
          DEFAULT: '#00209F',
          50: '#E6E9FF',
          100: '#CCD4FF',
          200: '#99A9FF',
          300: '#667DFF',
          400: '#3352FF',
          500: '#00209F',
          600: '#001A7F',
          700: '#001460',
          800: '#000D40',
          900: '#000720',
        },
        // Secondary color scale (Green - for success/secondary actions)
        secondary: {
          DEFAULT: '#009543',
          50: '#E6F7ED',
          100: '#CCEEDB',
          200: '#99DDB7',
          300: '#66CC93',
          400: '#33BB6F',
          500: '#009543',
          600: '#007736',
          700: '#005928',
          800: '#003C1B',
          900: '#001E0D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'bounce-subtle': 'bounceSubtle 0.5s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
    },
  },
  plugins: [],
}
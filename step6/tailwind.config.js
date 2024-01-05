/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './static-files/**/*.{html,js}',
    './static-files/daisyui/**/*.{html,js,ts,tsx,jsx}',
    ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
   daisyui: {
    themes: [
      "light",
      "dark"
    ],
  },
}
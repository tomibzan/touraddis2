/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './core/templates/**/*.html',
    './tours/templates/**/*.html',
    './marketplace/templates/**/*.html',
    './blog/templates/**/*.html',
    './inventory/templates/**/*.html',
    './reports/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'ethiopian-green': '#078930',
        'ethiopian-yellow': '#FCDD09',
        'ethiopian-red': '#DA121A',
      },
    },
  },
  plugins: [],
};

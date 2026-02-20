module.exports = {
  content: [
    "./src/**/*.{php,js,ts,tsx,css,scss}",
    "./Functionality/**/*.php",
    "./Components/**/*.php",
  ],
  theme: {
    extend: {
      colors: {},
    },
  },
  plugins: [],
  important: true,
  prefix: "pb-",
  corePlugins: {
    preflight: false,
  },
};

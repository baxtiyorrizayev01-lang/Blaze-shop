export default {
  content: ['./index.html','./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B0F17',
        card: 'rgba(255,255,255,0.04)',
        orange: '#FF6B00',
        'orange-light': '#FF8C00',
      },
      fontFamily: { sans: ['Barlow','system-ui','sans-serif'] }
    }
  },
  plugins: []
}

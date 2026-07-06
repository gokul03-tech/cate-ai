/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Legal navy blue palette
        primary: {
          50:  '#f0f5ff',
          100: '#e0eaff',
          200: '#b9ceff',
          300: '#8ab1fd',
          400: '#5a8ffb',
          500: '#3a70f5',
          600: '#2554e8',
          700: '#1e3a5f',
          800: '#172d4a',
          900: '#0f1f33',
          950: '#080f1a',
        },
        // Accent gold
        accent: {
          50:  '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        dark: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Georgia', 'serif'],
        mono: ['Fira Code', 'monospace'],
      },
      animation: {
        'fade-in':    'fadeIn 0.3s ease-in-out',
        'slide-up':   'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'spin-slow':  'spin 3s linear infinite',
        'bounce-slow':'bounce 2s infinite',
        'glow':       'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(20px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        glow:    { from: { boxShadow: '0 0 10px #3a70f540' }, to: { boxShadow: '0 0 30px #3a70f580' } },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}

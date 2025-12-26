/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ['Fredoka', 'sans-serif'],
        body: ['Quicksand', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        'sims-green': {
          DEFAULT: '#10A316',
          50: '#E7F6E8',
          100: '#CFF0D1',
          200: '#9FE1A3',
          300: '#6FD275',
          400: '#40C347',
          500: '#10A316',
          600: '#0D8A12',
          700: '#0A710E',
          800: '#07580B',
          900: '#052D06',
        },
        'sims-blue': '#00A4E4',
        'sims-red': '#E4002B',
        'plumbob': '#4C9F38',
        'dark-void': '#0B0F19',
        'surface-dark': '#151B2B',
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      animation: {
        'plumbob-float': 'plumbob-float 3s ease-in-out infinite',
        'pulse-green': 'pulse-green 2s infinite',
      },
      keyframes: {
        'plumbob-float': {
          '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
          '50%': { transform: 'translateY(-20px) rotate(5deg)' },
        },
        'pulse-green': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(16, 163, 22, 0.7)' },
          '50%': { boxShadow: '0 0 0 10px rgba(16, 163, 22, 0)' },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Georgia", "Cambria", "serif"],
        ui: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        fortress: {
          black: "#050506",
          ink: "#0b0d10",
          panel: "#111318",
          line: "#2c313a",
          text: "#f2efe8",
          muted: "#a3a09a",
          amber: "#d8b35d",
          blue: "#87a8c8",
          red: "#b86b61",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;

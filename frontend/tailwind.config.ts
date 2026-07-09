import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forgeai: {
          indigo: {
            DEFAULT: "#1a1a2e",
            50: "#e8e8f0",
            100: "#c5c5d6",
            200: "#9e9eb8",
            300: "#77779a",
            400: "#55557e",
            500: "#333362",
            600: "#2a2a52",
            700: "#1a1a2e",
            800: "#121220",
            900: "#0a0a14",
          },
          charcoal: {
            DEFAULT: "#16213e",
            50: "#e6e9f0",
            100: "#b8bfd4",
            200: "#8694b5",
            300: "#556996",
            400: "#304a7d",
            500: "#16213e",
            600: "#141d36",
            700: "#10172c",
            800: "#0c1122",
            900: "#080b18",
          },
          stone: {
            DEFAULT: "#e8e4e1",
            50: "#fdfcfc",
            100: "#faf9f8",
            200: "#f5f3f1",
            300: "#e8e4e1",
            400: "#d5d0cc",
            500: "#c2bbb6",
            600: "#a9a19b",
            700: "#8f867f",
            800: "#766c64",
            900: "#5c524a",
          },
          vermilion: {
            DEFAULT: "#c0392b",
            50: "#fdf0ee",
            100: "#f9d4d0",
            200: "#f0a49c",
            300: "#e67468",
            400: "#d94f40",
            500: "#c0392b",
            600: "#a33024",
            700: "#86271d",
            800: "#691e16",
            900: "#4c150f",
          },
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fade-in 0.6s ease-out forwards",
        "fade-in-delay": "fade-in 0.6s ease-out 0.15s forwards",
        "fade-in-delay-2": "fade-in 0.6s ease-out 0.3s forwards",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;

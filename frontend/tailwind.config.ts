import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./types/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        lab: "#09090b",
        ink: "#f8fafc",
        violet: "#7c3aed",
        cyanline: "#22d3ee"
      }
    }
  },
  plugins: []
};

export default config;

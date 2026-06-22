import nextVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = [
  ...nextVitals,
  {
    ignores: [".next/**", ".next/dev/**", "out/**", "build/**", "next-env.d.ts"]
  }
];

export default eslintConfig;

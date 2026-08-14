import js from "@eslint/js";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

const browserGlobals = {
  window: "readonly", document: "readonly", fetch: "readonly", localStorage: "readonly",
  console: "readonly", URLSearchParams: "readonly", FormData: "readonly", navigator: "readonly",
  AudioContext: "readonly", MediaRecorder: "readonly", Blob: "readonly", TextEncoder: "readonly",
  setInterval: "readonly", clearInterval: "readonly", setTimeout: "readonly", clearTimeout: "readonly",
};

export default [
  js.configs.recommended,
  {
    files: ["**/*.jsx", "**/*.js"],
    plugins: { react, "react-hooks": reactHooks },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: browserGlobals,
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "no-unused-vars": "warn",
    },
    settings: { react: { version: "19" } },
  },
];

// Doc comment rules for JavaScript and TypeScript: every exported function,
// class, and method carries a JSDoc comment that describes each parameter,
// the returned value, and what it throws. static-analysis.sh runs this config
// on top of the project's own linter. Tests document themselves through their
// names, so test files are left out.
import jsdoc from "eslint-plugin-jsdoc";
import tseslint from "typescript-eslint";

const exported = {
  publicOnly: true,
  require: {
    FunctionDeclaration: true,
    MethodDefinition: true,
    ClassDeclaration: true,
    ArrowFunctionExpression: true,
    FunctionExpression: true,
  },
};

export default [
  { ignores: ["**/*.test.*", "**/*.spec.*", "**/__tests__/**", "**/node_modules/**"] },
  {
    files: ["**/*.{js,jsx,mjs,cjs,ts,tsx,mts,cts}"],
    languageOptions: { parser: tseslint.parser },
    plugins: { jsdoc },
    rules: {
      "jsdoc/require-jsdoc": ["error", exported],
      "jsdoc/require-description": ["error", { contexts: ["any"] }],
      "jsdoc/require-param": "error",
      "jsdoc/require-param-description": "error",
      "jsdoc/check-param-names": "error",
      "jsdoc/require-returns": "error",
      "jsdoc/require-returns-description": "error",
      "jsdoc/require-throws": "error",
    },
  },
];

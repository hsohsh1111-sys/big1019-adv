import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import globals from "globals";

export default [
  js.configs.recommended, // ESLint 권장 규칙 (no-unused-vars, no-undef 등)
  {
    languageOptions: { ecmaVersion: 2022, sourceType: "module", globals: globals.node },
    rules: {
      eqeqeq: "error", // == 금지, === 사용
      "no-var": "error", // var 금지
      "prefer-const": "warn", // 재할당 없는 변수는 const
      "no-console": "off", // 실습용 CLI 프로그램이므로 허용
      complexity: ["warn", 6], // 함수 분기가 너무 많으면 경고
    },
  },
  prettier, // 스타일 관련 규칙은 끄고 Prettier에 맡김 (항상 마지막)
];

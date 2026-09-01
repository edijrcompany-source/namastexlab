// ESLint flat config — apps/web (Etapa 13)
// Guardrails de ARQUITETURA, não estética:
//  - jsx-no-literals: zero string crua (i18n — ADR-0009/Etapa 7 §5)
//  - no-dangerouslySetInnerHTML: XSS do chat (Etapa 10 T15)
import js from "@eslint/js";
import react from "eslint-plugin-react";

export default [
    js.configs.recommended,
    ...react.configs.flat.recommended,
    {
        files: ["**/*.{ts,tsx}"],
        languageOptions: {
            ecmaVersion: 2024,
            sourceType: "module",
        },
        settings: { react: { version: "detect" } },
        rules: {
            // i18n: texto de tela só do catálogo messages/pt-BR.json
            "react/jsx-no-literals": ["error", {
                noStrings: true,
                allowedProps: ["aria-label"],
                ignoreProps: true,
                noAttributeStrings: false,
            }],
            // XSS: texto do lead é hostil — React escapa; HTML cru proibido
            "react/no-danger": "error",
            // exções documentadas (Etapa 7 §5): símbolos/números técnicos
            "no-restricted-syntax": [
                "error",
                {
                    selector: "TemplateLiteral",
                    message: "Strings de tela saem do catálogo (messages/pt-BR.json) — sem template literals em JSX.",
                },
            ],
        },
    },
    {
        ignores: ["src/types/**"], // tipos GERADOS do contrato (Etapa 5) — nunca editar, nunca lintar
    },
];

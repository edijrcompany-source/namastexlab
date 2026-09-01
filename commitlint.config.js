// commitlint — padrão gitmoji (Etapa 13 §2)
// Formato: <gitmoji> <type>(escopo)?: <subject imperativo em inglês, <=72 chars>
const TYPES = ["feat", "fix", "test", "docs", "refactor", "perf", "security", "chore", "ci", "style", "build", "revert"];
const SCOPES = ["agent-api", "web", "contracts", "messages", "schemas", "docs", "ci", "data", "evals", "prompts", "repo"];

// aceita emoji unicode opcional + combo skin-tone/VS16 antes do type
const HEADER = new RegExp(
    String.raw`^(?:\p{Extended_Pictographic}[\uFE0F\u200D\p{Extended_Pictographic}]*\s)?` +
    String.raw`(\w+)(?:\(([\w-]+)\))?!?:\s(.+)$`,
    "u",
);

module.exports = {
    parserPreset: {
        parserOpts: {
            headerPattern: HEADER,
            headerCorrespondence: ["type", "scope", "subject"],
        },
    },
    plugins: [
        {
            rules: {
                // subject em imperativo: rejeita terminações comuns de passado/gerúndio
                "subject-imperative": ({ subject }) => {
                    const bad = /\b\w+(ed|ing)\b(\s|$)/i.test(subject || "");
                    return [!bad, "subject no imperativo em inglês (evite 'added', 'adding'…)"];
                },
                // exige o gitmoji — sem emoji, commit rejeitado
                "has-gitmoji": (parsed, _when, raw) => {
                    const ok = /^\p{Extended_Pictographic}/u.test((raw || "").trim());
                    return [ok, "commit deve começar com gitmoji (✨ feat, 🐛 fix, ✅ test…)"];
                },
            },
        },
    ],
    rules: {
        "type-empty": [2, "never"],
        "type-enum": [2, "always", TYPES],
        "scope-enum": [2, "always", SCOPES],
        "subject-empty": [2, "never"],
        "subject-full-stop": [2, "never", "."],
        "subject-imperative": [2],
        "has-gitmoji": [2],
        "header-max-length": [2, "always", 100],
    },
};

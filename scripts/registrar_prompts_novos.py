# Registra prompts novos (continuação do log incremental p40+)
import datetime
import io
import subprocess

P = [
(41,"status-obs-ci-cobertura","duvida","Foram implementados observabilidade e pipeline de CI/CD para commitar na main? O sistema está atingindo 99% de cobertura de teste?"),
(42,"regra-registrar-prompts","feedback","Não esqueça de registrar cada prompt nos ai-logs."),
]

for num, slug, cat, texto in P:
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    base = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    arq = f"ai-logs/prompts/p{num:02d}-{slug}.md"
    io.open(arq, "w", encoding="utf-8", newline="\n").write(
        f"""---
n: {num}
quando: {agora}  (base: {base})
categoria: {cat}
---

## Prompt (refinado)

{texto}

## Resultado

Registrado no log incremental; ver commit deste arquivo e o índice em prompts/README.md.
"""
    )
    subprocess.run(["git", "add", arq], check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", f"docs(ai-logs): register prompt p{num:02d} ({slug})"],
        check=True,
    )
print("OK", len(P), "novos prompts")

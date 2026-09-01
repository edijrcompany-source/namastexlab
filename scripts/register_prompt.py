#!/usr/bin/env python3
"""Registro incremental de prompts — REGRA DE NEGÓCIO OBRIGATÓRIA.

PRIMEIRA AÇÃO de todo novo prompt: registrar (file + índice + commit + push).
SEGUNDA AÇÃO: revisar arquitetura (nunca perder contexto).

Uso:
  python scripts/register_prompt.py <slug> <categoria> <texto>
  python scripts/register_prompt.py fix-bug "bug" "Descrição do prompt..."
"""
import datetime
import glob
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(ROOT, "ai-logs", "prompts")
INDEX_FILE = os.path.join(PROMPTS_DIR, "README.md")


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"git error: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


def next_prompt_number() -> int:
    files = glob.glob(os.path.join(PROMPTS_DIR, "p*.md"))
    files = [f for f in files if not f.endswith("README.md")]
    if not files:
        return 1
    nums = [int(re.search(r"p(\d+)", os.path.basename(f)).group(1)) for f in files]
    return max(nums) + 1


def update_index(num: int, slug: str, commit_sha: str) -> None:
    """Atualiza o índice dinâmicamente: linha nova + contador."""
    s = io.open(INDEX_FILE, encoding="utf-8").read()

    # atualiza contador no texto
    s = re.sub(r"\d+ prompts do autor", f"{num} prompts do autor", s)

    # adiciona linha na tabela
    linha = f"| p{num:02d} | {slug} | ver arquivo | `{commit_sha}` |"
    if linha not in s:
        # insere após a última linha da tabela (ou no fim)
        linhas = s.rstrip().split("\n")
        # encontra última linha que começa com "| p"
        last_table = 0
        for i, l in enumerate(linhas):
            if l.startswith("| p") or l.startswith("|---"):
                last_table = i
        linhas.insert(last_table + 1, linha)
        s = "\n".join(linhas) + "\n"

    io.open(INDEX_FILE, "w", encoding="utf-8", newline="\n").write(s)


def register(slug: str, categoria: str, texto: str) -> None:
    num = next_prompt_number()
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    base = git("rev-parse", "--short", "HEAD")
    arq = os.path.join(PROMPTS_DIR, f"p{num:02d}-{slug}.md")

    # YAML seguro: quando citado, commit_base em campo separado
    io.open(arq, "w", encoding="utf-8", newline="\n").write(
        f"""---
n: {num}
quando: "{agora}"
commit_base: "{base}"
categoria: {categoria}
---

## Prompt (refinado)

{texto}

## Resultado

Registrado via scripts/register_prompt.py (regra de negócio: primeira ação de todo prompt).
"""
    )

    # commit do arquivo do prompt
    git("add", arq)
    git("commit", "-q", "-m", f"docs(ai-logs): register prompt p{num:02d} ({slug})")
    sha = git("rev-parse", "--short", "HEAD")

    # atualiza índice + commit do índice
    update_index(num, slug, sha)
    git("add", INDEX_FILE)
    git("commit", "-q", "-m", f"docs(ai-logs): auto-update index to {num} prompts (p{num:02d})")

    # push (silencioso se falhar — não bloqueia o fluxo)
    subprocess.run(
        ["git", "-C", ROOT, "push", "-q"], capture_output=True
    )

    print(f"✅ p{num:02d} registrado · commit {sha} · índice atualizado · pushed")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python scripts/register_prompt.py <slug> <categoria> <texto>")
        sys.exit(1)
    register(sys.argv[1], sys.argv[2], sys.argv[3])

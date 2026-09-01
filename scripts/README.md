# scripts/ — pipelines de dados e ferramentas

- `fetch_bronze.(sh|py)` — regenera dataset Bronze do repo do desafio (T-08)
- `build_silver.py` — Bronze→Silver: masking + normalização + relatório (T-08, spec §7)
- `pseudo_locale.py` — gera pt-X-TEST e valida placeholders/limites/UTF-8 (Etapa 7 §6)

# viatges-cat

Anàlisi independent dels viatges a l'estranger dels alts càrrecs i del personal directiu de la Generalitat de Catalunya.

> **Aquest no és un web oficial.** Les dades provenen del conjunt
> [Viatges a l'estranger dels alts càrrecs i personal directiu de la Generalitat de Catalunya](https://analisi.transparenciacatalunya.cat/d/5kte-hque),
> publicat al portal de Dades Obertes de Catalunya, i es mostren amb finalitat informativa.
> Un viatge estadísticament atípic no implica cap irregularitat.

## Estat

🚧 **Fase 1 — Neteja i normalització.**

| Fase | Descripció | Estat |
|------|------------|-------|
| 0 | Ingesta en cru via API SODA i inventari de qualitat | ✅ |
| 1 | Neteja i normalització (destinacions, imports, dates) | 🚧 |
| 2 | Emmagatzematge i detecció de canvis entre instantànies | ⏳ |
| 3 | Automatització setmanal (GitHub Actions) | ⏳ |
| 4 | Web pública | ⏳ |
| 5 | Model de cost esperat i viatges atípics | ⏳ |

## Ús

Cal tenir [uv](https://docs.astral.sh/uv/).

```bash
uv sync                       # instal·la les dependències
cp .env.example .env          # opcional: hi afegeixes la teva SODA_APP_TOKEN
uv run viatges ingest         # descarrega una instantània a data/raw/
uv run viatges profile        # genera reports/fase0_inventari.md
uv run viatges clean          # genera data/processed/<instantània>/ i reports/fase1_neteja.md
uv run pytest                 # tests
```

## Estructura

```
src/viatges/
  config.py      configuració (dataset, rutes, token)
  soda.py        client de l'API SODA amb paginació i reintents
  schema.py      esquema esperat i mapatge de columnes de l'API
  ingest.py      descarrega instantànies en cru i immutables
  profiling.py   inventari de qualitat de les dades (Fase 0)
  clean.py       neteja i normalització (Fase 1, regles a l'ADR 0002)
  cli.py         ordres `viatges ingest`, `viatges profile` i `viatges clean`
data/manual/     diccionaris i correccions manuals (versionats)
docs/decisions/  registre de decisions d'arquitectura (ADR)
reports/         informes generats
notebooks/       exploració lliure (important el paquet)
```

## Font de les dades

[Dades Obertes de Catalunya](https://analisi.transparenciacatalunya.cat/d/5kte-hque) · Generalitat de Catalunya.
Consulta les condicions de reutilització al mateix portal.

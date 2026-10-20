# viatges-cat

Anàlisi independent dels viatges a l'estranger dels alts càrrecs i del personal directiu de la Generalitat de Catalunya.

> **Aquest no és un web oficial.** Les dades provenen del conjunt
> [Viatges a l'estranger dels alts càrrecs i personal directiu de la Generalitat de Catalunya](https://analisi.transparenciacatalunya.cat/d/5kte-hque),
> publicat al portal de Dades Obertes de Catalunya, i es mostren amb finalitat informativa.
> Un viatge estadísticament atípic no implica cap irregularitat.


## Criteris de l'anàlisi

Les dades s'analitzen **tal com les publica la Generalitat**. No es corregeix cap valor: els
problemes detectats (duplicats, imports incomplets, errors de data…) queden marcats en
columnes a part. L'única exclusió són els viatges amb una durada per sobre del percentil 99
(ara mateix, més d'11 dies), que són majoritàriament errors de data.
Detalls a [docs/decisions/0004-dades-tal-com-venen.md](docs/decisions/0004-dades-tal-com-venen.md).

## Ús

Cal tenir [uv](https://docs.astral.sh/uv/).

```bash
uv sync                       # instal·la les dependències
cp .env.example .env          # opcional: hi afegeixes la teva SODA_APP_TOKEN
uv run viatges ingest         # descarrega una instantània a data/raw/
uv run viatges profile        # genera reports/fase0_inventari.md
uv run viatges prepare        # genera data/processed/<instantània>/ i reports/fase1_preparacio.md
uv run viatges changes        # compara les dues darreres instantànies -> reports/canvis/
uv run viatges build          # reconstrueix data/viatges.sqlite a partir de totes les instantànies
uv run viatges update         # ingest + changes + prepare + build
uv run viatges pull           # recupera de Turso les instantànies que falten en local
uv run viatges push           # puja instantànies noves i taules derivades a Turso
uv run viatges web            # genera el web estàtic a site/
uv run python -m http.server 8000 --directory site   # previsualitza el web
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
  prepare.py     preparació per a l'anàlisi (Fase 1, ADR 0004)
  changes.py     detecció de canvis entre instantànies (Fase 2, ADR 0003)
  store.py       base de dades SQLite derivada (Fase 2, ADR 0003)
  turso.py       còpia a Turso per HTTP (Fase 3, ADR 0005)
  site/          generador del web estàtic: plantilles, CSS i JS (Fase 4, ADR 0006)
  cli.py         ordres `viatges ingest|profile|prepare|changes|build|update|pull|push|web`
data/manual/     diccionaris i anotacions manuals (versionats)
docs/decisions/  registre de decisions d'arquitectura (ADR)
reports/         informes generats
notebooks/       exploració lliure (important el paquet)
```

## Automatització i Turso

Cada dilluns, el workflow [`actualitzacio.yml`](.github/workflows/actualitzacio.yml) executa
`pull` → `update` → `push` i desa els informes a `reports/`. També es pot llançar a mà des de
la pestanya *Actions* de GitHub.

Configuració inicial (un sol cop):

1. Crea un compte a [turso.tech](https://turso.tech) (pla gratuït) i instal·la la CLI:
   `brew install tursodatabase/tap/turso` i després `turso auth login`.
2. Crea la base de dades i obtén-ne l'URL i un token de lectura i escriptura:
   ```bash
   turso db create viatges-cat
   turso db show viatges-cat --url
   turso db tokens create viatges-cat
   ```
3. Posa `TURSO_URL` i `TURSO_TOKEN` al fitxer `.env` i fes la primera càrrega des de local,
   perquè l'arxiu de Turso comenci amb les instantànies que ja tens:
   `uv run viatges build && uv run viatges push`.
4. A GitHub, *Settings → Secrets and variables → Actions*, crea els secrets `TURSO_URL`,
   `TURSO_TOKEN`, `SODA_APP_TOKEN` i `SODA_APP_SECRET` (o amb `gh secret set NOM`).

## Web

Mentre es treballa, el web es revisa en local:

```bash
uv run viatges web && uv run python -m http.server 8000 --directory site
```

El workflow [`web.yml`](.github/workflows/web.yml) publica la web:

- **sol, cada dilluns**, després de l'actualització setmanal de dades, de manera que les xifres
  publicades es mantenen al dia sense intervenció;
- **a mà** (*Actions → Web → Run workflow*), per publicar canvis de disseny o de textos.

Els push no despleguen res. Cal tenir en compte, però, que el desplegament del dilluns publica
el codi que hi hagi a `main` en aquell moment. Configuració
de Vercel (un sol cop):

1. A Vercel, crea un projecte nou amb el framework «Other». No hi connectis el repositori
   de Git: el web es construeix a GitHub Actions perquè necessita les dades de Turso.
2. Des de la carpeta del projecte, executa `npx vercel link` i copia `orgId` i `projectId`
   de `.vercel/project.json`.
3. Crea un token a *Vercel → Account Settings → Tokens*.
4. A GitHub, *Settings → Secrets and variables → Actions*: crea els secrets `VERCEL_TOKEN`,
   `VERCEL_ORG_ID` i `VERCEL_PROJECT_ID`, i la variable `PUBLICAR_WEB` = `true`.

## Font de les dades

[Dades Obertes de Catalunya](https://analisi.transparenciacatalunya.cat/d/5kte-hque) · Generalitat de Catalunya.
Consulta les condicions de reutilització al mateix portal.

Mapa base: [Natural Earth](https://www.naturalearthdata.com/) 1:110m (domini públic), simplificat a
`src/viatges/site/geo/paisos-110m.json`.

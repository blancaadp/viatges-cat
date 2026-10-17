# viatges-cat

Análisis independiente de los viajes al extranjero de los altos cargos y del personal directivo de la Generalitat de Catalunya.

> **Esta no es una web oficial.** Los datos provienen del conjunto
> [Viatges a l'estranger dels alts càrrecs i personal directiu de la Generalitat de Catalunya](https://analisi.transparenciacatalunya.cat/d/5kte-hque),
> publicado en el portal de Dades Obertes de Catalunya, y se muestran con finalidad informativa.
> Un viaje estadísticamente atípico no implica ninguna irregularidad.

## Estado

🚧 **Fase 1 — Limpieza y normalización.**

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Ingesta cruda vía API SODA e inventario de calidad | ✅ |
| 1 | Limpieza y normalización (destinos, importes, fechas) | 🚧 |
| 2 | Almacenamiento y detección de cambios entre instantáneas | ⏳ |
| 3 | Automatización semanal (GitHub Actions) | ⏳ |
| 4 | Web pública | ⏳ |
| 5 | Modelo de coste esperado y viajes atípicos | ⏳ |

## Uso

Requiere [uv](https://docs.astral.sh/uv/).

```bash
uv sync                       # instala dependencias
cp .env.example .env          # opcional: añade tu SODA_APP_TOKEN
uv run viatges ingest         # descarga una instantánea en data/raw/
uv run viatges profile        # genera reports/fase0_inventario.md
uv run viatges clean          # genera data/processed/<instantánea>/ y reports/fase1_neteja.md
uv run pytest                 # tests
```

## Estructura

```
src/viatges/
  config.py      configuración (dataset, rutas, token)
  soda.py        cliente de la API SODA con paginación y reintentos
  schema.py      esquema esperado y mapeo de columnas de la API
  ingest.py      descarga instantáneas crudas e inmutables
  profiling.py   inventario de calidad de datos (Fase 0)
  clean.py       limpieza y normalización (Fase 1, reglas en el ADR 0002)
  cli.py         comandos `viatges ingest`, `viatges profile` y `viatges clean`
data/manual/     diccionarios y correcciones manuales (versionados)
docs/decisions/  registro de decisiones de arquitectura (ADR)
reports/         informes generados
notebooks/       exploración libre (importando el paquete)
```

## Fuente de datos

[Dades Obertes de Catalunya](https://analisi.transparenciacatalunya.cat/d/5kte-hque) · Generalitat de Catalunya.
Consulta las condiciones de reutilización en el propio portal.

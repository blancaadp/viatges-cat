# 0003 · Detecció de canvis i emmagatzematge en SQLite

**Estat:** acceptada

## Context

Amb dues instantànies (2026-09-29 i 2026-10-17) ja veiem com evoluciona el dataset:

- 17 altes i cap baixa. Algunes altes són viatges de fa mesos (raccERGO-2127, d'octubre de
  2025, publicat l'octubre de 2026): **el retard de publicació** és informació en si mateix.
- 3 modificacions de text en registres existents (una errata corregida, dues observacions
  afegides). El portal no avisa d'aquests canvis.

Per a la Fase 4 (web) cal un format que es pugui consultar sense pandas.

## Decisió

1. **Les instantànies en cru continuen sent la font de veritat** (ADR 0001). Tot el que ve
   després es pot regenerar.
2. **Detecció de canvis entre instantànies consecutives**, a nivell de dada en cru i per `id`:
   - `alta`: l'id apareix per primera vegada.
   - `baixa`: l'id ja no hi és.
   - `modificacio`: una fila per camp canviat, amb el valor anterior i el nou. Es compara el
     text sense espais als extrems; un camp buit i un camp absent compten igual.
   Cada execució deixa un informe a `reports/canvis/<instantània>.md`.
3. **Base de dades SQLite derivada** a `data/viatges.sqlite`, que es reconstrueix sencera a
   partir de totes les instantànies (`viatges build`). No s'actualitza de manera incremental:
   així sempre és coherent amb les instantànies i amb les regles de neteja vigents.

   | Taula | Contingut |
   |---|---|
   | `instantanies` | Una fila per instantània (manifest: data, files, hash). |
   | `viatges` | Viatges preparats de la darrera instantània (ADR 0004) + `primera_aparicio`, `dies_fins_publicacio`. |
   | `trams` | Destinacions normalitzades de la darrera instantània. |
   | `canvis` | Historial d'altes, baixes i modificacions entre instantànies consecutives. |
   | `historial_ids` | Per id: primera i darrera instantània on apareix, i si encara hi és. |

4. **Retard de publicació.** `primera_aparicio` és la data de la primera instantània on surt
   l'id. Per als registres que ja hi eren a la primera instantània no sabem quan es van
   publicar, i `dies_fins_publicacio` queda buit (no s'inventa). Per a la resta,
   `dies_fins_publicacio = primera_aparicio − data_fi`. És una cota superior: amb
   instantànies setmanals l'error és de com a molt 7 dies. Els duplicats queden buits, perquè
   la seva aparició és una republicació.

## Conseqüències

- `viatges update` encadena ingesta, informe de canvis, preparació i reconstrucció de la base de dades:
  és l'ordre que executarà l'automatització de la Fase 3.
- La base de dades no es versiona a git (`data/` està exclosa), però es pot regenerar en
  segons.
- **Pendent per a la Fase 3:** on es desen les instantànies quan la ingesta corri a GitHub
  Actions. Ara només són en local; si es perden, es perd l'historial de canvis. S'ha decidit
  fer una còpia en una base de dades allotjada (Turso, compatible amb SQLite), com fa
  contractes-cat.
- La ingesta escriu primer en una carpeta temporal i la reanomena al final, perquè una
  descàrrega fallida no deixi carpetes buides a `data/raw/`.

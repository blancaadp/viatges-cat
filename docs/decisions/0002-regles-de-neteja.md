# 0002 · Regles de neteja (sortida de la Fase 0)

**Estat:** acceptada — implementada a `src/viatges/clean.py`

## Context

L'inventari de qualitat (`reports/fase0_inventari.md`, instantània del 2026-09-29, 1.511
files) mostra problemes en imports, dates, duplicats, destinacions, departaments i camps de
text. Aquest document fixa què cal fer amb cadascun.

## Principis generals

1. **La dada en cru no es toca.** La neteja produeix columnes noves (`*_clean`, `pais`,
   `ciutat`…) a partir de la instantània; les columnes originals es conserven.
2. **Marcar abans que esborrar.** No s'elimina cap registre: els problemes s'assenyalen amb
   columnes booleanes `flag_*`, i cada anàlisi decideix si els exclou. Així el web pot
   explicar per què un viatge no entra en un càlcul.
3. **Regles generals al codi, excepcions en un fitxer.** El que es resol amb una regla va a
   `src/viatges/clean.py` amb tests; el que només es pot decidir cas per cas va a
   `data/manual/correccions.csv` (`id, camp, valor_nou, motiu, font`), versionat a git. Mai
   no es corregeix una dada a mà sense deixar-ne el motiu escrit.
4. **No inventar.** Si una dada no es pot deduir amb seguretat, queda com a desconeguda
   (`NaN`), no com a 0.

## Regles per problema

### 1. Imports

| Problema | Casos | Regla | Per què |
|---|---|---|---|
| Partides o total buits | ACC001, ACC003, ACC004 | Si falta el total i hi ha totes les partides → `total_clean = suma`. Si falta alguna partida i hi ha el total → partida = `NaN` (no 0). Si falten el total i alguna partida → `total_clean = NaN`, `flag_import_incomplet`. | Omplir amb 0 infravaloraria el cost. |
| Suma de partides ≠ total | racc-1725, racc-1768 (diferència de 2 €) | Si `\|diferència\| ≤ 5 €` → s'accepta el **total publicat** i es marca `flag_redondeig`. Si és més gran → `flag_import_inconsistent` i revisió manual. | Les diferències petites són arrodoniments de cèntims; el total és la xifra oficial. |
| Total = 0 | 101 | Classificar amb `observacions` a `motiu_import_zero`: **`imputat_a_altre`** ("s'imputen al registre del viatge del MHP", "inclòs en el viatge de la consellera"), **`pagat_per_tercers`** ("assumides per l'Incasol", "a càrrec d'ACCIÓ"), **`pendent`** ("en curs d'elaboració", "s'estan gestionant") → `total_clean = NaN`, **`sense_despesa`** (la resta). | Un 0 "pendent" no és un viatge gratuït, i un d'"imputat a un altre" no ha de comptar com a viatge barat a les comparatives. |
| Imports negatius / no numèrics | 0 | Cap acció; el test de la Fase 1 ha de fallar si n'apareixen. | Vigilar regressions en noves instantànies. |
| Imports molt alts (màx. 134.778 €) | — | No es corregeixen. Es tracten a la Fase 5 (model de cost esperat). | Poden ser comitives grans; atípic ≠ error. |

### 2. Dates

| Problema | Casos | Regla | Per què |
|---|---|---|---|
| Dates il·legibles, fi < inici, inici futur | 0 | Cap acció; un test ha de fallar si n'apareixen. | — |
| Viatges de més de 21 dies | 5 (racc-950, racc-340, racc-1364, racc-1699, racc-1148) | `flag_durada_sospitosa`. Exclosos de les mètriques per dia (cost/dia). Correcció només via `correccions.csv` si el `motiu`/`agenda` o una altra font deixa clara la data real. | Gairebé segur que són errates, però corregir sense font seria inventar. |
| Revisió 2026-10-17 | Els 5 anteriors | Tots cinc eren errors de mes o de data de fi i s'han corregit a `correccions.csv` amb la font de cadascun (agenda del mateix registre, viatges de la mateixa persona que s'encavalquen, dates públiques de l'esdeveniment). racc-1699 té confiança mitjana. | — |
| Data amb hora `T00:00:00.000` | totes | Desar `data_inici`/`data_fi` com a `date` sense hora. Durada = `data_fi − data_inici + 1`. | L'hora no aporta informació. |

### 3. Duplicats

Hi ha quatre prefixos d'id que corresponen a sistemes de registre diferents: `CMH` (gen–ago 2018),
`ACC` (oct 2018–mar 2019), `racc` (2017–2026) i `raccERGO` (des d'oct 2023).

| Cas | Regla |
|---|---|
| Mateixa persona (`nom`) i `data_inici` **i mateix total** (CMH020/racc-31, CMH024/racc-94, CMH049/racc-150, racc-1455/racc-1701, racc-1118/racc-1131…) | **Duplicat real.** Se'n conserva un (preferència: `racc*` sobre `CMH`/`ACC`, perquè té la destinació més ben informada; entre dos `racc`, l'id més baix) i l'altre es marca `flag_duplicat` amb `duplicat_de = <id>`. S'exclou de sumes i recomptes. La clau no inclou la destinació perquè CMH049/racc-150 la tenen escrita diferent. |
| Mateixa persona i data **amb totals diferents** | **No es fusiona.** S'agrupen amb un `grup_viatge` comú i `flag_possible_desdoblament`. Poden ser el mateix viatge imputat a dues unitats, o correccions publicades com a registre nou; es revisa cas per cas i s'anota a `correccions.csv`. Per als recomptes de "nombre de viatges" el grup es compta una vegada; per a la despesa, se sumen mentre no es demostri que és un duplicat. |
| Revisió manual | La decisió de cada grup s'anota a `correccions.csv` amb dos camps que no existeixen al dataset: `revisio_duplicat_de = <id que es conserva>` o `revisio_desdoblament = complementari \| independent \| pendent`. **Complementari**: mateix desplaçament amb els costos repartits (p. ex. dues ciutats consecutives), se sumen i compten com un viatge. **Independent**: viatges diferents, cadascun el seu grup. **Pendent**: revisat sense resoldre; continua marcat. Entre dues versions gairebé idèntiques es conserva la més recent, perquè és la correcció. Quan un registre inclou costos pagats per tercers (racc-904, Sucre), es compta el cost total del viatge. |

### 4. Destinacions

L'objectiu és passar de `destinacio` (text lliure) a una taula `trams` amb una fila per tram:
`id, ordre, ciutat, pais, iso2`.

| Problema | Regla |
|---|---|
| Diverses destinacions en un camp (139 viatges) | Separar per `/`, `;` o salt de línia **fora de parèntesis**, i també just després d'un `(país)` si darrere ve una altra destinació ("Tànger (Marroc) i Rabat (Marroc)"). Les comes soles no tallen — així no es trenquen "Washington, D.C." ni "Oliena (Sardenya, Itàlia)". Els casos sense parèntesis ("Tòquio, Himeji") es corregeixen a `correccions.csv`. |
| Variants de ciutat (Brussel·les / Brussels / BRUSSEL·LES / Brussel.les…) | Normalització mecànica (NFC, espais, majúscules, `l.l`→`l·l`) i després un diccionari `data/manual/ciutats.csv` (`variant → ciutat`) en català. Les variants no mapejades es llisten a l'informe per anar-lo completant. |
| Països escrits de manera diferent ("Estats Units, els", "Estats Units d'Amèrica", "EUA") | Diccionari `data/manual/paisos.csv` → nom en català + codi ISO 3166-1 alfa-2. L'ISO és la clau per a mapes i agregats. |
| Trams sense país ("Madrid", "Perpinyà", "Japó", "Catalunya Nord") | Deduir el país des de `ciutats.csv`. Si el tram és un país ("Japó"), `ciutat = NaN`. Madrid es marca `flag_no_estranger` (no és l'estranger; es manté però s'exclou de les mètriques "a l'estranger"). |
| Problemes de codificació (`Gda?sk`, `Atmak?r`) | Correcció via `ciutats.csv` (`Gda?sk → Gdańsk`). L'informe ha de continuar avisant si apareixen nous `?`. |
| Soroll de puntuació (`"`, `.` finals, "Marrroc") | Treure cometes i punts finals mecànicament; errors d'escriptura via diccionari. |
| Falsos positius de l'heurística (Saint-Louis/Saint-Malo, New York City/New York Mills) | No es fusionen: l'heurística de 5 lletres només serveix per revisar; la unificació la decideix el diccionari. |

### 5. Departaments

No apareix com a problema a l'informe, però hi ha 39 noms perquè cada legislatura els
reanomena (p. ex. cinc variants d'Acció Exterior). Regla: conservar `departament` tal com és i
afegir `ambit` (estable entre legislatures: Acció Exterior, Cultura, Empresa, Presidència…)
mitjançant `data/manual/departaments.csv`. De passada, corregir variants tipogràfiques
("Igualtat i Feminisme" / "Igualtat i Feminismes").

### 6. Persones i càrrecs

284 persones i 312 càrrecs diferents. Normalitzar `nom` (espais, NFC, majúscules) per
agrupar; no fusionar noms diferents sense revisió. Afegir una `persona_id` estable via
`data/manual/persones.csv` només si es detecten variants de la mateixa persona.

### 7. Camps de text amb farciment

| Camp | Regla |
|---|---|
| `observacions`, `comitiva`, `altres_despeses_detall`, `agenda` | Valors de farciment (`-`, `--`, `.`, `0`, `Cap`, `Sense`, `Sense comitiva`, `No`, `x`, `Sense observacions`… sense distingir majúscules) → `NaN` a la columna `*_clean`. La llista viu en un únic lloc (`placeholder_mask`) i s'amplia amb tests. |
| `comitiva` | Fase posterior: estimar `n_persones_comitiva` (1 + persones llistades) per poder calcular el cost per persona. Fins aleshores el cost és "per registre", i el web ho ha de dir. |

## Conseqüències

- La Fase 1 crea `src/viatges/clean.py`, els diccionaris de `data/manual/` i tests per a
  cada regla d'aquest document.
- L'informe de la Fase 0 es regenera a cada ingesta; aquest document no, per això les
  decisions viuen aquí i no a l'informe.
- Quan una nova instantània porti un problema no cobert, s'afegeix una fila a aquest
  document abans de tocar el codi.

# 0002 · Reglas de limpieza (salida de la Fase 0)

**Estado:** aceptada — implementada en `src/viatges/clean.py`

## Contexto

El inventario de calidad (`reports/fase0_inventario.md`, instantánea del 2026-09-29, 1.511
filas) muestra problemas en importes, fechas, duplicados, destinos, departamentos y campos de
texto. Este documento fija qué hacer con cada uno.

## Principios generales

1. **El dato crudo no se toca.** La limpieza produce columnas nuevas (`*_clean`, `pais`,
   `ciutat`…) a partir de la instantánea; las columnas originales se conservan.
2. **Marcar antes que borrar.** Ningún registro se elimina: los problemas se señalan con
   columnas booleanas `flag_*`, y cada análisis decide si los excluye. Así la web puede
   explicar por qué un viaje no entra en un cálculo.
3. **Reglas generales en código, excepciones en un fichero.** Lo que se resuelve con una regla
   va en `src/viatges/clean.py` con tests; lo que solo se puede decidir caso a caso va en
   `data/manual/correcciones.csv` (`id, campo, valor_nuevo, motivo, fuente`), versionado en
   git. Nunca se corrige un dato a mano sin dejar el motivo escrito.
4. **No inventar.** Si un dato no se puede deducir con seguridad, queda como desconocido
   (`NaN`), no como 0.

## Reglas por problema

### 1. Importes

| Problema | Casos | Regla | Por qué |
|---|---|---|---|
| Partidas o total vacíos | ACC001, ACC003, ACC004 | Si falta el total y todas las partidas existen → `total_clean = suma`. Si falta alguna partida y el total existe → partida = `NaN` (no 0). Si falta el total y alguna partida → `total_clean = NaN`, `flag_import_incomplet`. | Rellenar con 0 infravaloraría el coste. |
| Suma de partidas ≠ total | racc-1725, racc-1768 (diferencia de 2 €) | Si `|diferencia| ≤ 5 €` → se acepta el **total publicado** y se marca `flag_redondeig`. Si es mayor → `flag_import_inconsistent` y revisión manual. | Diferencias pequeñas son redondeos de céntimos; el total es la cifra oficial. |
| Total = 0 | 101 | Clasificar con `observacions` en `motiu_import_zero`: **`imputat_a_altre`** ("s'imputen al registre del viatge del MHP", "inclòs en el viatge de la consellera"), **`pagat_per_tercers`** ("assumides per l'Incasol", "a càrrec d'ACCIÓ"), **`pendent`** ("en curs d'elaboració", "s'estan gestionant") → `total_clean = NaN`, **`sense_despesa`** (el resto). | Un 0 "pendiente" no es un viaje gratis, y uno "imputado a otro" no debe contar como viaje barato en las comparativas. |
| Importes negativos / no numéricos | 0 | Sin acción; el test de la Fase 1 debe fallar si aparecen. | Vigilar regresiones en nuevas instantáneas. |
| Importes muy altos (máx. 134.778 €) | — | No se corrigen. Se tratan en la Fase 5 (modelo de coste esperado). | Pueden ser comitivas grandes; atípico ≠ error. |

### 2. Fechas

| Problema | Casos | Regla | Por qué |
|---|---|---|---|
| Fechas no legibles, fin < inicio, inicio futuro | 0 | Sin acción; test que falle si aparecen. | — |
| Viajes de más de 21 días | 5 (racc-950, racc-340, racc-1364, racc-1699, racc-1148) | `flag_durada_sospitosa`. Excluidos de métricas por día (coste/día). Corrección solo vía `correcciones.csv` si el `motiu`/`agenda` deja clara la fecha real (p. ej. racc-1364, inauguración en Venecia: 17/04→19/09 parece un error de mes; racc-1148, Perpinyà con observación "Dia de feina" y total 0). | Casi seguro son erratas, pero corregir sin fuente sería inventar. |
| Fecha con hora `T00:00:00.000` | todas | Guardar `data_inici`/`data_fi` como `date` sin hora. Duración = `data_fi − data_inici + 1`. | La hora no aporta información. |

### 3. Duplicados

Hay cuatro prefijos de id que corresponden a sistemas de registro distintos: `CMH` (ene–ago 2018),
`ACC` (oct 2018–mar 2019), `racc` (2017–2026) y `raccERGO` (desde oct 2023).

| Caso | Regla |
|---|---|
| Mismo `nom` + `data_inici` + destino **y mismo total** (CMH020/racc-31, CMH024/racc-94, CMH049/racc-150, racc-1455/racc-1701, racc-1118/racc-1131) | **Duplicado real.** Se conserva uno (preferencia: `racc*` sobre `CMH`/`ACC`, por tener destino mejor informado; entre dos `racc`, el de id menor) y el otro se marca `flag_duplicat` con `duplicat_de = <id>`. Se excluye de sumas y recuentos. |
| Misma persona, fecha y destino **con totales distintos** (Portaceli, Cirici, Lacasta, Peña López) | **No se fusiona.** Se agrupan con un `grup_viatge` común y `flag_possible_desdoblament`. Pueden ser el mismo viaje imputado a dos unidades, o correcciones publicadas como registro nuevo; se revisa caso a caso y se anota en `correcciones.csv`. Para recuentos de "número de viajes" se cuenta el grupo una vez; para el gasto, se suman mientras no se demuestre que es duplicado. |
| Revisión manual | La decisión de cada grupo se anota en `correcciones.csv` con dos campos que no existen en el dataset: `revisio_duplicat_de = <id que se conserva>` o `revisio_desdoblament = complementari \| independent \| pendent`. **Complementari**: mismo desplazamiento con los costes repartidos (p. ej. dos ciudades consecutivas), se suman y cuentan como un viaje. **Independent**: viajes distintos, cada uno su grupo. **Pendent**: revisado sin resolver; sigue marcado. Entre dos versiones casi idénticas se conserva la más reciente, por ser la corrección. Cuando un registro incluye costes pagados por terceros (racc-904, Sucre), se cuenta el coste total del viaje. |
| La clave de detección | Se ampliará a `nom` + `data_inici` (sin destino), porque CMH049/racc-150 tienen el destino escrito distinto y la regla actual no los detecta. |

### 4. Destinos

El objetivo es pasar de `destinacio` (texto libre) a una tabla `trams` con una fila por tramo:
`id, ordre, ciutat, pais, iso2`.

| Problema | Regla |
|---|---|
| Varios destinos en un campo (139 viajes) | Separar por `/`, `;` y ` i ` **fuera de paréntesis**. La coma solo separa si cada lado tiene su propio `(país)` — así no se rompen "Washington, D.C." ni "Oliena (Sardenya, Itàlia)". |
| Variantes de ciudad (Brussel·les / Brussels / BRUSSEL·LES / Brussel.les…) | Normalización mecánica (NFC, espacios, mayúsculas, `l.l`→`l·l`) y luego un diccionario `data/manual/ciutats.csv` (`variant → ciutat_canonica`) en catalán. Las variantes no mapeadas se listan en el informe para irlo completando. |
| Países escritos distinto ("Estats Units, els", "Estats Units d'Amèrica", "EUA") | Diccionario `data/manual/paisos.csv` → nombre en catalán + código ISO 3166-1 alfa-2. El ISO es la clave para mapas y agregados. |
| Tramos sin país ("Madrid", "Perpinyà", "Japó", "Catalunya Nord") | Deducir el país desde `ciutats.csv`. Si el tramo es un país ("Japó"), `ciutat = NaN`. Madrid se marca `flag_no_estranger` (no es extranjero; se mantiene pero se excluye de las métricas "a l'estranger"). |
| Problemas de codificación (`Gda?sk`, `Atmak?r`) | Corrección vía `ciutats.csv` (`Gda?sk → Gdańsk`). El informe debe seguir avisando si aparecen nuevos `?`. |
| Ruido de puntuación (`"`, `.` finales, "Marrroc") | Quitar comillas y puntos finales mecánicamente; errores de escritura vía diccionario. |
| Falsos positivos de la heurística (Saint-Louis/Saint-Malo, New York City/New York Mills) | No se fusionan: la heurística de 5 letras solo sirve para revisar; la unificación la decide el diccionario. |

### 5. Departamentos

No aparece como problema en el informe, pero hay 39 nombres porque cada legislatura los
renombra (p. ej. cinco variantes de Acción Exterior). Regla: conservar `departament` tal cual y
añadir `ambit` (estable entre legislaturas: Acció Exterior, Cultura, Empresa, Presidència…)
mediante `data/manual/departaments.csv`. Corregir de paso variantes tipográficas ("Igualtat i
Feminisme" / "Igualtat i Feminismes").

### 6. Personas y cargos

284 personas y 312 cargos distintos. Normalizar `nom` (espacios, NFC, mayúsculas) para
agrupar; no fusionar nombres distintos sin revisión. Añadir una `persona_id` estable vía
`data/manual/persones.csv` solo si se detectan variantes de la misma persona.

### 7. Campos de texto con relleno

| Campo | Regla |
|---|---|
| `observacions`, `comitiva`, `altres_despeses_detall`, `agenda` | Valores de relleno (`-`, `--`, `.`, `0`, `Cap`, `Sense`, `Sense comitiva`, `No`, `x`, `Sense observacions`… sin distinguir mayúsculas) → `NaN` en la columna `*_clean`. La lista vive en un único sitio (`placeholder_mask`) y se amplía con tests. |
| `comitiva` | Fase posterior: estimar `n_persones_comitiva` (1 + personas listadas) para poder calcular coste por persona. Hasta entonces el coste es "por registro", y la web lo debe decir. |

## Consecuencias

- La Fase 1 crea `src/viatges/clean.py`, los diccionarios de `data/manual/` y tests para cada
  regla de este documento.
- El informe de Fase 0 se regenera en cada ingesta; este documento no, por eso las decisiones
  viven aquí y no en el informe.
- Cuando una nueva instantánea traiga un problema no cubierto, se añade una fila a este
  documento antes de tocar el código.

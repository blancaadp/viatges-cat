# Fase 1 · Resultado de la limpieza

_Instantánea descargada el 2026-09-29T16:51:11.327707+00:00. Reglas: [ADR 0002](../docs/decisions/0002-reglas-de-limpieza.md)._

- Viajes: **1511** · tramos de destino: **1733**
- Correcciones manuales aplicadas: 23
- Ciudades distintas tras normalizar: 327 (antes 403)
- Países distintos: 82
- Departamentos sin ámbito asignado: 0

## Señales (`flag_*`)

|                            |   registros |
|:---------------------------|------------:|
| flag_total_calculat        |           1 |
| flag_redondeig             |           2 |
| flag_import_inconsistent   |           0 |
| flag_import_incomplet      |          12 |
| flag_durada_sospitosa      |           0 |
| flag_duplicat              |          14 |
| flag_possible_desdoblament |           2 |
| flag_desti_sense_pais      |           0 |
| flag_no_estranger          |           5 |

## Motivo de los importes a cero

| motiu_import_zero   |   count |
|:--------------------|--------:|
| sense_despesa       |      52 |
| imputat_a_altre     |      22 |
| pagat_per_tercers   |      17 |
| pendent             |      10 |

## Duplicados descartados

| id            | duplicat_de   | nom                       |   total_clean |
|:--------------|:--------------|:--------------------------|--------------:|
| racc-1036     | racc-1053     | Carme Portaceli           |        684.92 |
| racc-689      | racc-787      | Teresa Jordà i Roura      |          0    |
| racc-934      | racc-933      | Josep Vidal i Fàbrega     |       1010.6  |
| CMH049        | racc-150      | Laura Borràs i Castanyer  |        512.52 |
| CMH024        | racc-94       | Natàlia Mas Guix          |        786.75 |
| CMH020        | racc-31       | Ernest Maragall i Mira    |      14298.2  |
| racc-178      | racc-151      | Laura Borràs i Castanyer  |        584.67 |
| racc-1098     | racc-904      | Ismael Peña López         |        140.4  |
| racc-1131     | racc-1118     | Bernat Costas Castilla    |        777.76 |
| racc-1701     | racc-1455     | Aleix Cubells Barceló     |        465.34 |
| racc-1735     | raccERGO-2037 | Andrea Costafreda Quesada |       1364.7  |
| raccERGO-2039 | raccERGO-2061 | Carme Portaceli           |         72.6  |
| raccERGO-1855 | racc-1633     | Laura Foraster i Lloret   |      29906.8  |
| raccERGO-2095 | raccERGO-2128 | Alberto Lacasta Huelin    |       4379.48 |

## Posibles desdoblamientos (revisar)

| grup_viatge   | id            | nom                     | data_inici_clean   |   total_clean |
|:--------------|:--------------|:------------------------|:-------------------|--------------:|
| raccERGO-2047 | raccERGO-2047 | Elisabet Cirici i Amell | 2026-05-19         |       1657.8  |
| raccERGO-2047 | raccERGO-2068 | Elisabet Cirici i Amell | 2026-05-19         |       1371.03 |

## Pendiente de completar en `data/manual/`

### Países sin mapear (`paisos.csv`)

_Ninguno._

### Tramos sin país

_Ninguno._

### Ciudades que aún parecen variantes (`ciutats.csv`, heurística)

| clau   | variants                                        |   n_variants |   n_registres |
|:-------|:------------------------------------------------|-------------:|--------------:|
| saint  | Saint-Gaudens | Saint-Louis | Saint-Malo        |            3 |             5 |
| canne  | Cannes | Cannes-Écluse                          |            2 |            10 |
| monte  | Montecarlo | Montevideo                         |            2 |             8 |
| santi  | Santiago | Santiago de Querétaro                |            2 |             4 |
| portl  | Port Louis | Port-la-Nouvelle                   |            2 |             2 |
| reggi  | Reggio Calabria | Reggio nell'Emilia            |            2 |             2 |
| santa  | Santa Coloma d'Andorra | Santander de Quilichao |            2 |             2 |
| villa  | Villach | Villavicencio                         |            2 |             2 |

### Departamentos sin ámbito (`departaments.csv`)

_Ninguno._

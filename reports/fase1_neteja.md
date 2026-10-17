# Fase 1 · Resultat de la neteja

_Instantània descarregada el 2026-09-29T16:51:11.327707+00:00. Regles: [ADR 0002](../docs/decisions/0002-regles-de-neteja.md)._

- Viatges: **1511** · trams de destinació: **1733**
- Correccions manuals aplicades: 23
- Ciutats diferents després de normalitzar: 327 (abans 403)
- Països diferents: 82
- Departaments sense àmbit assignat: 0

## Senyals (`flag_*`)

|                            |   registres |
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

## Motiu dels imports a zero

| motiu_import_zero   |   count |
|:--------------------|--------:|
| sense_despesa       |      52 |
| imputat_a_altre     |      22 |
| pagat_per_tercers   |      17 |
| pendent             |      10 |

## Duplicats descartats

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

## Possibles desdoblaments (revisar)

| grup_viatge   | id            | nom                     | data_inici_clean   |   total_clean |
|:--------------|:--------------|:------------------------|:-------------------|--------------:|
| raccERGO-2047 | raccERGO-2047 | Elisabet Cirici i Amell | 2026-05-19         |       1657.8  |
| raccERGO-2047 | raccERGO-2068 | Elisabet Cirici i Amell | 2026-05-19         |       1371.03 |

## Pendent de completar a `data/manual/`

### Països sense mapejar (`paisos.csv`)

_Cap._

### Trams sense país

_Cap._

### Ciutats que encara semblen variants (`ciutats.csv`, heurística)

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

### Departaments sense àmbit (`departaments.csv`)

_Cap._

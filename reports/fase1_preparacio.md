# Fase 1 · Preparació de les dades

_Instantània descarregada el 2026-10-19T11:35:03.923689+00:00. Les dades s'analitzen tal com venen: vegeu l'[ADR 0004](../docs/decisions/0004-dades-tal-com-venen.md)._

- Viatges: **1529** · trams de destinació: **1753**
- Exclosos de l'anàlisi (durada > p99 = 11 dies): **13**, que sumen 46,582 € de 4,861,124 €
- Registres amb anotacions manuals: 20
- Ciutats diferents després de normalitzar: 330 (abans 410)
- Països diferents: 83
- Departaments sense àmbit assignat: 0

## Viatges exclosos de l'anàlisi

| id            | nom                          | data_inici_iso   | data_fi_iso   |   durada_dies |
|:--------------|:-----------------------------|:-----------------|:--------------|--------------:|
| racc-1364     | Pere Almeda i Samaranch      | 2024-04-17       | 2024-09-19    |           156 |
| raccERGO-2107 | Jaume Duch Guillot           | 2026-05-05       | 2026-08-08    |            96 |
| racc-1148     | Roger Torrent i Ramió        | 2024-01-19       | 2024-03-19    |            61 |
| racc-950      | Núria Vergés Bosch           | 2023-05-10       | 2023-07-04    |            56 |
| racc-1699     | Gerard Graells del Bas       | 2025-11-03       | 2025-12-09    |            37 |
| racc-340      | Maria Àngels Chacón i Feixas | 2019-10-04       | 2019-11-05    |            33 |
| racc-1488     | Carme Portaceli              | 2025-03-30       | 2025-04-13    |            15 |
| racc-1644     | Oriol Lázaro Llovera         | 2025-03-20       | 2025-04-03    |            15 |
| racc-1487     | Carme Portaceli              | 2025-03-12       | 2025-03-26    |            15 |
| racc-843      | Carme Portaceli              | 2023-01-22       | 2023-02-03    |            13 |
| racc-54       | David Ferrer i Canosa        | 2018-09-12       | 2018-09-23    |            12 |
| racc-1027     | Roger Torrent i Ramió        | 2023-10-10       | 2023-10-21    |            12 |
| racc-1332     | Jean-Marc Segarra i Mauri    | 2024-04-11       | 2024-04-22    |            12 |

## Senyals (`flag_*`)

|                            |   registres |
|:---------------------------|------------:|
| flag_redondeig             |           2 |
| flag_import_inconsistent   |           0 |
| flag_import_incomplet      |           3 |
| flag_duplicat              |          16 |
| flag_possible_desdoblament |           4 |
| flag_desti_sense_pais      |           0 |
| flag_no_estranger          |           5 |
| flag_tram_repetit          |           4 |

## Motiu dels imports a zero

| motiu_import_zero   |   count |
|:--------------------|--------:|
| sense_despesa       |      52 |
| imputat_a_altre     |      22 |
| pagat_per_tercers   |      18 |
| pendent             |      10 |

## Duplicats marcats

| id            | duplicat_de   | nom                       |   total_eur |
|:--------------|:--------------|:--------------------------|------------:|
| racc-1036     | racc-1053     | Carme Portaceli           |      684.92 |
| racc-689      | racc-787      | Teresa Jordà i Roura      |        0    |
| racc-934      | racc-933      | Josep Vidal i Fàbrega     |     1010.6  |
| CMH049        | racc-150      | Laura Borràs i Castanyer  |      512.52 |
| CMH024        | racc-94       | Natàlia Mas Guix          |      786.75 |
| CMH020        | racc-31       | Ernest Maragall i Mira    |    14298.2  |
| racc-178      | racc-151      | Laura Borràs i Castanyer  |      584.67 |
| racc-1098     | racc-904      | Ismael Peña López         |      140.4  |
| racc-1131     | racc-1118     | Bernat Costas Castilla    |      777.76 |
| racc-1701     | racc-1455     | Aleix Cubells Barceló     |      465.34 |
| racc-1735     | raccERGO-2037 | Andrea Costafreda Quesada |     1364.7  |
| raccERGO-2039 | raccERGO-2061 | Carme Portaceli           |       72.6  |
| raccERGO-1855 | racc-1633     | Laura Foraster i Lloret   |    29906.8  |
| raccERGO-2095 | raccERGO-2128 | Alberto Lacasta Huelin    |     4379.48 |
| raccERGO-2136 | raccERGO-2016 | Clelia Colombo Vilarrasa  |     5639.11 |
| raccERGO-1824 | racc-1597     | Sònia Hernández Almodóvar |     3240    |

## Possibles desdoblaments (revisar)

| grup_viatge   | id            | nom                     | data_inici_iso   |   total_eur |
|:--------------|:--------------|:------------------------|:-----------------|------------:|
| racc-2        | CMH018        | Jordi Foz Dalmau        | 2018-07-17       |     3636.25 |
| racc-2        | racc-2        | Jordi Foz i Dalmau      | 2018-07-17       |     1167.97 |
| raccERGO-2047 | raccERGO-2047 | Elisabet Cirici i Amell | 2026-05-19       |     1657.8  |
| raccERGO-2047 | raccERGO-2068 | Elisabet Cirici i Amell | 2026-05-19       |     1371.03 |

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
| nanji  | Nanjiang | Nanjing                              |            2 |             2 |
| portl  | Port Louis | Port-la-Nouvelle                   |            2 |             2 |
| reggi  | Reggio Calabria | Reggio nell'Emilia            |            2 |             2 |
| santa  | Santa Coloma d'Andorra | Santander de Quilichao |            2 |             2 |
| villa  | Villach | Villavicencio                         |            2 |             2 |

### Departaments sense àmbit (`departaments.csv`)

_Cap._

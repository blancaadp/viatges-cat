# Fase 0 · Inventari de qualitat de les dades

_Generat el 2026-10-17 18:21 UTC a partir de la instantània descarregada el 2026-10-17T18:13:55.520019+00:00._

## Resum

- Files: **1528**
- Darrera actualització de files segons el portal: 2026-10-16T09:31:11+00:00
- Interval de dates d'inici: 2017-01-29 → 2026-09-16
- Departaments diferents: 39 · Persones diferents: 285
- Columnes inesperades a l'esquema: cap
- Columnes esperades que falten: cap

## Imports

- Registres sense total: 2
- Registres amb total 0: 102
- Imports negatius: 0
- Registres on la suma de partides no coincideix amb el total: 2

|      | id        |   dietes |   allotjament |   transport |   altres_despeses |   total |   diferencia |
|-----:|:----------|---------:|--------------:|------------:|------------------:|--------:|-------------:|
| 1385 | racc-1725 |      682 |          1912 |        4164 |                 0 |    6760 |            2 |
| 1389 | racc-1768 |      176 |           857 |        1057 |               465 |    2557 |            2 |

### Valors que no es poden llegir com a número

```
{
  "dietes": {},
  "allotjament": {},
  "transport": {},
  "altres_despeses": {},
  "total": {}
}
```

### Estadístics descriptius

|                 |   count |    mean |     std |   min |    25% |     50% |     75% |    max |
|:----------------|--------:|--------:|--------:|------:|-------:|--------:|--------:|-------:|
| dietes          |    1527 |  182.53 |  398.89 |     0 |   0    |   60.6  |  179.13 |   6000 |
| allotjament     |    1528 |  956.38 | 2500.37 |     0 | 117.08 |  350.25 |  864    |  37720 |
| transport       |    1528 | 1628.89 | 4875.55 |     0 | 256.12 |  489.34 | 1351.93 | 102653 |
| altres_despeses |    1526 |  415.07 | 1523.36 |     0 |   0    |   45.14 |  164.19 |  33708 |
| total           |    1526 | 3183.34 | 8002.69 |     0 | 570.74 | 1056.62 | 2731.88 | 134778 |

### Mateix import en registres diferents (despesa compartida?)

|    | columna   |   import | ids                                      |
|---:|:----------|---------:|:-----------------------------------------|
|  0 | dietes    |     6.45 | racc-765, racc-430                       |
|  1 | dietes    |     7.5  | racc-960, CMH044                         |
|  2 | dietes    |     8.2  | racc-1485, racc-1503                     |
|  3 | dietes    |    13.9  | racc-352, racc-202                       |
|  4 | dietes    |    14    | racc-737, racc-1293                      |
|  5 | dietes    |    14.55 | CMH024, racc-94                          |
|  6 | dietes    |    15    | raccERGO-1960, raccERGO-2049             |
|  7 | dietes    |    16    | racc-715, racc-878                       |
|  8 | dietes    |    18.4  | CMH090, CMH001                           |
|  9 | dietes    |    18.85 | racc-394, racc-1246                      |
| 10 | dietes    |    19    | racc-1673, racc-1727                     |
| 11 | dietes    |    19.4  | racc-349, racc-789, racc-1455, racc-1701 |
| 12 | dietes    |    19.8  | racc-356, racc-1659                      |
| 13 | dietes    |    21.1  | racc-451, racc-557                       |
| 14 | dietes    |    21.5  | racc-369, racc-879, racc-1281            |
| 15 | dietes    |    22.3  | racc-868, racc-541                       |
| 16 | dietes    |    22.5  | racc-123, racc-109                       |
| 17 | dietes    |    22.8  | racc-469, racc-1121                      |
| 18 | dietes    |    23.3  | racc-875, racc-1420                      |
| 19 | dietes    |    24    | racc-402, racc-827                       |
| 20 | dietes    |    25.15 | racc-743, racc-262                       |
| 21 | dietes    |    26    | racc-339, racc-1295                      |
| 22 | dietes    |    26.9  | CMH062, racc-1239                        |
| 23 | dietes    |    27.2  | racc-360, racc-1684                      |
| 24 | dietes    |    29    | racc-755, racc-433, CMH052               |

## Dates

Valors que no es poden llegir com a data:

```
{
  "data_inici": {},
  "data_fi": {}
}
```

- Dates d'inici en el futur: 0
- Registres amb el final anterior a l'inici: 0

_Cap._

Durada en dies (inclosos):

|       |      0 |
|:------|-------:|
| count | 1527   |
| mean  |    3.4 |
| std   |    5.5 |
| min   |    1   |
| 25%   |    2   |
| 50%   |    3   |
| 75%   |    4   |
| max   |  156   |

Viatges de més de 21 dies (revisar):

|      | id            | destinacio                                | data_inici          | data_fi             |
|-----:|:--------------|:------------------------------------------|:--------------------|:--------------------|
|  345 | racc-950      | Bolzano (Itàlia)                          | 2023-05-10 00:00:00 | 2023-07-04 00:00:00 |
|  545 | racc-340      | Londres (Regne Unit)                      | 2019-10-04 00:00:00 | 2019-11-05 00:00:00 |
| 1217 | racc-1364     | Venice (Itàlia)                           | 2024-04-17 00:00:00 | 2024-09-19 00:00:00 |
| 1325 | racc-1699     | Bogotá (Colòmbia)                         | 2025-11-03 00:00:00 | 2025-12-09 00:00:00 |
| 1395 | racc-1148     | Perpinyà (França)                         | 2024-01-19 00:00:00 | 2024-03-19 00:00:00 |
| 1511 | raccERGO-2107 | Brussel·les (Bèlgica)Brussel·les (França) | 2026-05-05 00:00:00 | 2026-08-08 00:00:00 |

## Duplicats

- Ids duplicats: 0
- Mateixa persona, data i destinació: 20 registres

|      | id            | nom                       | data_inici              | destinacio                         |
|-----:|:--------------|:--------------------------|:------------------------|:-----------------------------------|
|   76 | racc-1036     | Carme Portaceli           | 2023-11-13T00:00:00.000 | Brussels (Bèlgica)                 |
|   81 | racc-1053     | Carme Portaceli           | 2023-11-13T00:00:00.000 | Brussels (Bèlgica)                 |
|  106 | racc-1118     | Bernat Costas Castilla    | 2024-01-23T00:00:00.000 | Stockholm (Suècia)                 |
|  672 | CMH024        | Natàlia Mas Guix          | 2018-07-10T00:00:00.000 | Edimburg (Regne Unit)              |
|  673 | racc-94       | Natàlia Mas Guix          | 2018-07-10T00:00:00.000 | Edimburg (Regne Unit)              |
|  677 | CMH020        | Ernest Maragall i Mira    | 2018-07-14T00:00:00.000 | Nova York (Estats Units d'Amèrica) |
|  679 | racc-31       | Ernest Maragall i Mira    | 2018-07-14T00:00:00.000 | Nova York (Estats Units d'Amèrica) |
|  837 | racc-1098     | Ismael Peña López         | 2022-11-20T00:00:00.000 | Sucre (Bolívia)                    |
|  838 | racc-904      | Ismael Peña López         | 2022-11-20T00:00:00.000 | Sucre (Bolívia)                    |
| 1072 | racc-1131     | Bernat Costas Castilla    | 2024-01-23T00:00:00.000 | Stockholm (Suècia)                 |
| 1139 | racc-1455     | Aleix Cubells Barceló     | 2025-02-19T00:00:00.000 | Brussels (Bèlgica)                 |
| 1326 | racc-1701     | Aleix Cubells Barceló     | 2025-02-19T00:00:00.000 | Brussels (Bèlgica)                 |
| 1404 | racc-1597     | Sònia Hernández Almodóvar | 2025-07-10T00:00:00.000 | Humlebæk (Dinamarca)               |
| 1431 | raccERGO-2039 | Carme Portaceli           | 2026-05-03T00:00:00.000 | Budapest (Hongria)                 |
| 1446 | raccERGO-2047 | Elisabet Cirici i Amell   | 2026-05-19T00:00:00.000 | Baku (Azerbaidjan)                 |
| 1449 | raccERGO-2061 | Carme Portaceli           | 2026-05-03T00:00:00.000 | Budapest (Hongria)                 |
| 1459 | raccERGO-2068 | Elisabet Cirici i Amell   | 2026-05-19T00:00:00.000 | Baku (Azerbaidjan)                 |
| 1496 | raccERGO-2095 | Alberto Lacasta Huelin    | 2026-07-31T00:00:00.000 | Amsterdam (Països Baixos)          |
| 1506 | raccERGO-2128 | Alberto Lacasta Huelin    | 2026-07-31T00:00:00.000 | Amsterdam (Països Baixos)          |
| 1525 | raccERGO-1824 | Sònia Hernández Almodóvar | 2025-07-10T00:00:00.000 | Humlebæk (Dinamarca)               |

## Destinacions

- Valors diferents del camp destinació: 471
- Viatges amb diverses destinacions: 141

### Trams sense país entre parèntesis

| tram                                                                          |   count |
|:------------------------------------------------------------------------------|--------:|
| Madrid                                                                        |       4 |
| Brussel·les                                                                   |       2 |
| Perpinyà                                                                      |       1 |
| Stocolm                                                                       |       1 |
| Buenos Aires (Argentina) Montevideo (Uruguai)                                 |       1 |
| TOLOUSE                                                                       |       1 |
| BONN                                                                          |       1 |
| LONDRES                                                                       |       1 |
| Catalunya Nord                                                                |       1 |
| Berlin                                                                        |       1 |
| Japó                                                                          |       1 |
| Oliena (Sardenya, Itàlia)"                                                    |       1 |
| Brussel.les                                                                   |       1 |
| Tòquio, Himeji                                                                |       1 |
| Bratislava (Eslovàquia).                                                      |       1 |
| Ministeri de Cultura, Joventut i Esports del Govern Andorrà, Andorra la Vella |       1 |
| Mònaco                                                                        |       1 |
| París                                                                         |       1 |
| Tànger (Marrroc) i Rabat (Marroc)                                             |       1 |
| Tokio                                                                         |       1 |

### Possibles problemes de codificació

|     | tram             |
|----:|:-----------------|
| 105 | Gda?sk (Polònia) |
| 318 | Gda?sk (Polònia) |
| 457 | Atmak?r (Índia)  |

### Possibles variants de la mateixa ciutat (heurística, revisar)

| clau   | variants                                                          |   n_variants |   n_registres |
|:-------|:------------------------------------------------------------------|-------------:|--------------:|
| bruss  | "Brussel·les | BRUSSEL·LES | Brussel.les | Brussels | Brussel·les |            5 |           371 |
| washi  | Washington | Washington D.C. | Washington DC | Washington, D.C.   |            4 |            18 |
| berli  | Berlin | Berlin Köpenick | Berlín                                 |            3 |            37 |
| copen  | Copenhagen | Copenhaghen | Copenhaguen                            |            3 |            17 |
| marse  | Marseille | Marseille 10 | Marsella                               |            3 |            16 |
| munic  | Munic | Munich | Múnic                                            |            3 |            14 |
| saint  | Saint-Gaudens | Saint-Louis | Saint-Malo                          |            3 |             5 |
| paris  | Paris | París                                                     |            2 |            79 |
| lisbo  | Lisboa | Lisbon                                                   |            2 |            42 |
| newyo  | New York City | New York Mills                                    |            2 |            32 |
| andor  | Andorra la Vella | Andorra la vella                               |            2 |            30 |
| londr  | LONDRES | Londres                                                 |            2 |            29 |
| perpi  | Perpignan | Perpinyà                                              |            2 |            26 |
| amste  | Amsterdam | Àmsterdam                                             |            2 |            19 |
| dubli  | Dublin | Dublín                                                   |            2 |            11 |
| canne  | Cannes | Cannes-Écluse                                            |            2 |            10 |
| gineb  | GINEBRA | Ginebra                                                 |            2 |            10 |
| bogot  | Bogotà | Bogotá                                                   |            2 |             9 |
| estra  | Estrasbug | Estrasburg                                            |            2 |             8 |
| telav  | Tel Aviv | Tel-Aviv                                               |            2 |             8 |

### Països més freqüents (tal com vénen escrits)

| pais                   |   count |
|:-----------------------|--------:|
| Bèlgica                |     376 |
| França                 |     229 |
| Itàlia                 |     113 |
| Alemanya               |      95 |
| Regne Unit             |      83 |
| Estats Units, els      |      71 |
| Portugal               |      60 |
| Suïssa                 |      55 |
| Japó                   |      42 |
| Àustria                |      40 |
| Andorra                |      36 |
| Estats Units d'Amèrica |      33 |
| Xina                   |      33 |
| Mèxic                  |      31 |
| Països Baixos          |      29 |

## Camps de text: nuls i valors de farciment

|                        |   nuls |   farciment_o_buits |   valors_diferents |
|:-----------------------|-------:|--------------------:|-------------------:|
| observacions           |    109 |                1026 |                477 |
| comitiva               |     61 |                 571 |                909 |
| altres_despeses_detall |     83 |                 462 |                753 |
| agenda                 |     26 |                  39 |               1414 |
| carrec                 |      0 |                   0 |                313 |
| departament            |      0 |                   0 |                 39 |
| destinacio             |      0 |                   0 |                471 |
| id                     |      0 |                   0 |               1528 |
| motiu                  |      0 |                   0 |               1335 |
| nom                    |      0 |                   0 |                285 |
| unitat_organica        |      0 |                   0 |                239 |

## Decisions de neteja

_Les regles per a cada problema d'aquest informe són a [docs/decisions/0002-regles-de-neteja.md](../docs/decisions/0002-regles-de-neteja.md). Si apareix un problema nou, afegeix-lo allà abans de tocar el codi._

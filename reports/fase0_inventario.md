# Fase 0 · Inventario de calidad de datos

_Generado el 2026-10-17 17:38 UTC a partir de la instantánea descargada el 2026-09-29T16:51:11.327707+00:00._

## Resumen

- Filas: **1511**
- Última actualización de filas según el portal: 2026-09-29T09:28:48+00:00
- Rango de fechas de inicio: 2017-01-29 → 2026-09-10
- Departamentos distintos: 39 · Personas distintas: 284
- Columnas inesperadas en el esquema: ninguna
- Columnas esperadas que faltan: ninguna

## Importes

- Registros sin total: 2
- Registros con total 0: 101
- Importes negativos: 0
- Registros donde la suma de partidas no coincide con el total: 2

|      | id        |   dietes |   allotjament |   transport |   altres_despeses |   total |   diferencia |
|-----:|:----------|---------:|--------------:|------------:|------------------:|--------:|-------------:|
| 1385 | racc-1725 |      682 |          1912 |        4164 |                 0 |    6760 |            2 |
| 1389 | racc-1768 |      176 |           857 |        1057 |               465 |    2557 |            2 |

### Valores que no se pueden leer como número

```
{
  "dietes": {},
  "allotjament": {},
  "transport": {},
  "altres_despeses": {},
  "total": {}
}
```

### Estadísticos descriptivos

|                 |   count |    mean |     std |   min |    25% |     50% |     75% |    max |
|:----------------|--------:|--------:|--------:|------:|-------:|--------:|--------:|-------:|
| dietes          |    1510 |  181.97 |  397.73 |     0 |   0    |   60.58 |  178.73 |   6000 |
| allotjament     |    1511 |  958.89 | 2512.83 |     0 | 115.53 |  350    |  864    |  37720 |
| transport       |    1511 | 1614.22 | 4844.2  |     0 | 253.71 |  489.1  | 1344.44 | 102653 |
| altres_despeses |    1509 |  413.18 | 1524.67 |     0 |   0    |   44.3  |  162.1  |  33708 |
| total           |    1509 | 3168.72 | 7986.02 |     0 | 570.02 | 1055.75 | 2720.86 | 134778 |

### Mismo importe en registros distintos (¿gasto compartido?)

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

## Fechas

Valores que no se pueden leer como fecha:

```
{
  "data_inici": {},
  "data_fi": {}
}
```

- Fechas de inicio en el futuro: 0
- Registros con fin anterior al inicio: 0

_Ninguno._

Duración en días (inclusive):

|       |      0 |
|:------|-------:|
| count | 1510   |
| mean  |    3.4 |
| std   |    5   |
| min   |    1   |
| 25%   |    2   |
| 50%   |    3   |
| 75%   |    4   |
| max   |  156   |

Viajes de más de 21 días (revisar):

|      | id        | destinacio           | data_inici          | data_fi             |
|-----:|:----------|:---------------------|:--------------------|:--------------------|
|  345 | racc-950  | Bolzano (Itàlia)     | 2023-05-10 00:00:00 | 2023-07-04 00:00:00 |
|  545 | racc-340  | Londres (Regne Unit) | 2019-10-04 00:00:00 | 2019-11-05 00:00:00 |
| 1217 | racc-1364 | Venice (Itàlia)      | 2024-04-17 00:00:00 | 2024-09-19 00:00:00 |
| 1325 | racc-1699 | Bogotá (Colòmbia)    | 2025-11-03 00:00:00 | 2025-12-09 00:00:00 |
| 1395 | racc-1148 | Perpinyà (França)    | 2024-01-19 00:00:00 | 2024-03-19 00:00:00 |

## Duplicados

- Ids duplicados: 0
- Misma persona, fecha y destino: 18 registros

|      | id            | nom                     | data_inici              | destinacio                         |
|-----:|:--------------|:------------------------|:------------------------|:-----------------------------------|
|   76 | racc-1036     | Carme Portaceli         | 2023-11-13T00:00:00.000 | Brussels (Bèlgica)                 |
|   81 | racc-1053     | Carme Portaceli         | 2023-11-13T00:00:00.000 | Brussels (Bèlgica)                 |
|  106 | racc-1118     | Bernat Costas Castilla  | 2024-01-23T00:00:00.000 | Stockholm (Suècia)                 |
|  672 | CMH024        | Natàlia Mas Guix        | 2018-07-10T00:00:00.000 | Edimburg (Regne Unit)              |
|  673 | racc-94       | Natàlia Mas Guix        | 2018-07-10T00:00:00.000 | Edimburg (Regne Unit)              |
|  677 | CMH020        | Ernest Maragall i Mira  | 2018-07-14T00:00:00.000 | Nova York (Estats Units d'Amèrica) |
|  679 | racc-31       | Ernest Maragall i Mira  | 2018-07-14T00:00:00.000 | Nova York (Estats Units d'Amèrica) |
|  837 | racc-1098     | Ismael Peña López       | 2022-11-20T00:00:00.000 | Sucre (Bolívia)                    |
|  838 | racc-904      | Ismael Peña López       | 2022-11-20T00:00:00.000 | Sucre (Bolívia)                    |
| 1072 | racc-1131     | Bernat Costas Castilla  | 2024-01-23T00:00:00.000 | Stockholm (Suècia)                 |
| 1139 | racc-1455     | Aleix Cubells Barceló   | 2025-02-19T00:00:00.000 | Brussels (Bèlgica)                 |
| 1326 | racc-1701     | Aleix Cubells Barceló   | 2025-02-19T00:00:00.000 | Brussels (Bèlgica)                 |
| 1431 | raccERGO-2039 | Carme Portaceli         | 2026-05-03T00:00:00.000 | Budapest (Hongria)                 |
| 1446 | raccERGO-2047 | Elisabet Cirici i Amell | 2026-05-19T00:00:00.000 | Baku (Azerbaidjan)                 |
| 1449 | raccERGO-2061 | Carme Portaceli         | 2026-05-03T00:00:00.000 | Budapest (Hongria)                 |
| 1459 | raccERGO-2068 | Elisabet Cirici i Amell | 2026-05-19T00:00:00.000 | Baku (Azerbaidjan)                 |
| 1496 | raccERGO-2095 | Alberto Lacasta Huelin  | 2026-07-31T00:00:00.000 | Amsterdam (Països Baixos)          |
| 1506 | raccERGO-2128 | Alberto Lacasta Huelin  | 2026-07-31T00:00:00.000 | Amsterdam (Països Baixos)          |

## Destinos

- Valores distintos del campo destino: 465
- Viajes con varios destinos: 139

### Tramos sin país entre paréntesis

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

### Posibles problemas de codificación

|     | tram             |
|----:|:-----------------|
| 105 | Gda?sk (Polònia) |
| 318 | Gda?sk (Polònia) |
| 457 | Atmak?r (Índia)  |

### Posibles variantes de la misma ciudad (heurística, revisar)

| clau   | variants                                                          |   n_variants |   n_registres |
|:-------|:------------------------------------------------------------------|-------------:|--------------:|
| bruss  | "Brussel·les | BRUSSEL·LES | Brussel.les | Brussels | Brussel·les |            5 |           368 |
| washi  | Washington | Washington D.C. | Washington DC | Washington, D.C.   |            4 |            18 |
| berli  | Berlin | Berlin Köpenick | Berlín                                 |            3 |            36 |
| copen  | Copenhagen | Copenhaghen | Copenhaguen                            |            3 |            17 |
| marse  | Marseille | Marseille 10 | Marsella                               |            3 |            16 |
| munic  | Munic | Munich | Múnic                                            |            3 |            14 |
| saint  | Saint-Gaudens | Saint-Louis | Saint-Malo                          |            3 |             5 |
| paris  | Paris | París                                                     |            2 |            77 |
| lisbo  | Lisboa | Lisbon                                                   |            2 |            42 |
| newyo  | New York City | New York Mills                                    |            2 |            32 |
| andor  | Andorra la Vella | Andorra la vella                               |            2 |            30 |
| londr  | LONDRES | Londres                                                 |            2 |            29 |
| perpi  | Perpignan | Perpinyà                                              |            2 |            26 |
| amste  | Amsterdam | Àmsterdam                                             |            2 |            19 |
| dubli  | Dublin | Dublín                                                   |            2 |            11 |
| canne  | Cannes | Cannes-Écluse                                            |            2 |            10 |
| bogot  | Bogotà | Bogotá                                                   |            2 |             9 |
| gineb  | GINEBRA | Ginebra                                                 |            2 |             9 |
| estra  | Estrasbug | Estrasburg                                            |            2 |             8 |
| telav  | Tel Aviv | Tel-Aviv                                               |            2 |             8 |

### Países más frecuentes (tal como vienen escritos)

| pais                   |   count |
|:-----------------------|--------:|
| Bèlgica                |     373 |
| França                 |     226 |
| Itàlia                 |     113 |
| Alemanya               |      94 |
| Regne Unit             |      83 |
| Estats Units, els      |      69 |
| Portugal               |      59 |
| Suïssa                 |      54 |
| Japó                   |      42 |
| Àustria                |      38 |
| Andorra                |      36 |
| Estats Units d'Amèrica |      33 |
| Mèxic                  |      31 |
| Xina                   |      30 |
| Països Baixos          |      29 |

## Campos de texto: nulos y valores de relleno

|                        |   nulos |   relleno_o_vacios |   valores_distintos |
|:-----------------------|--------:|-------------------:|--------------------:|
| observacions           |     108 |               1025 |                 465 |
| comitiva               |      61 |                562 |                 903 |
| altres_despeses_detall |      83 |                461 |                 746 |
| agenda                 |      26 |                 39 |                1398 |
| carrec                 |       0 |                  0 |                 312 |
| departament            |       0 |                  0 |                  39 |
| destinacio             |       0 |                  0 |                 465 |
| id                     |       0 |                  0 |                1511 |
| motiu                  |       0 |                  0 |                1319 |
| nom                    |       0 |                  0 |                 284 |
| unitat_organica        |       0 |                  0 |                 238 |

## Decisiones de limpieza

_Las reglas para cada problema de este informe están en [docs/decisions/0002-reglas-de-limpieza.md](../docs/decisions/0002-reglas-de-limpieza.md). Si aparece un problema nuevo, añádelo allí antes de tocar el código._

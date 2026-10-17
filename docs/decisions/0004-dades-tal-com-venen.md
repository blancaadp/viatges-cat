# 0004 · Analitzar les dades tal com venen

**Estat:** acceptada · substitueix en part l'ADR 0002

## Context

L'ADR 0002 corregia valors (dates, destinacions, imports pendents) a partir de regles i
d'una revisió manual. Seguint l'enfocament de [contractes-cat](https://github.com/gerardgimenezadsuar/contractes-cat),
volem que l'anàlisi reflecteixi el que publica la Generalitat, sense que les nostres
correccions canviïn cap xifra.

També volíem treure els viatges molt llargs. Es va considerar tallar pel percentil 90 de la
durada, però amb les dades del 2026-10-17 el p90 és de 6 dies: el tall hauria tret 114
viatges (el 7%) que sumen el **25% de la despesa**, gairebé tots viatges legítims a l'Amèrica
o l'Àsia. El p99 (11 dies) només afecta els casos extrems.

## Decisió

1. **Valors tal com venen.** Només es converteixen els imports (`*_eur`) i les dates
   (`data_inici_iso`, `data_fi_iso`) de text a número o data. No s'omple cap total buit ni
   es buida cap import.
2. **Marques, no correccions.** Tot el que abans corregia ara és una columna afegida que no
   modifica res:
   - `flag_*`: duplicats, desdoblaments, imports incomplets o inconsistents, tram repetit,
     viatge no a l'estranger…
   - `motiu_import_zero`: per què un total és 0.
   - `correccio_<camp>`: el valor que la revisió manual considera correcte, amb el motiu i la
     font a `data/manual/correccions.csv`. Serveix de referència; l'anàlisi no l'utilitza.
   - `revisio_*`: decisions sobre duplicats i desdoblaments (ADR 0002, apartat 3).
3. **Columnes derivades.** La normalització de destinacions (taula `trams`, amb ciutat, país
   i codi ISO) i l'àmbit del departament (`ambit`) es mantenen: no canvien el valor
   publicat, però sense elles no es pot agregar per país ni per àmbit.
4. **Exclusió única: durada per sobre del p99.** `exclos_analisi = durada_dies > p99`, amb
   el p99 calculat a cada construcció sobre la instantània vigent. Els registres exclosos
   es conserven a la base de dades. Cap altra marca no exclou res: és cada anàlisi la que
   decideix si, per exemple, treu els duplicats.

## Conseqüències

- `clean.py` passa a ser `prepare.py` i l'ordre `viatges clean` passa a ser
  `viatges prepare`, perquè ja no neteja.
- Els errors de data coneguts (raccERGO-2107, 96 dies; racc-1364, 156 dies…) queden fora de
  l'anàlisi pel p99, sense haver-los de corregir.
- Les correccions de destinació que només servien per assignar un país es mouen al
  diccionari `ciutats.csv`, que és on viu la normalització.
- El llindar del p99 es pot moure si arriben nous viatges llargs; l'informe de preparació
  el mostra a cada execució.

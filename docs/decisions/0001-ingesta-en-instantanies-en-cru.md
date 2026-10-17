# 0001 · Ingesta en instantànies en cru i immutables

**Estat:** acceptada

## Context

El dataset s'actualitza periòdicament i els registres existents es poden corregir o
eliminar. L'API no ofereix cap historial de canvis.

## Decisió

Cada ingesta descarrega el dataset complet via API SODA i el desa sense modificar a
`data/raw/<timestamp>/`, juntament amb les metadades del portal i un manifest amb el hash.
Tota la neteja es fa després, a partir d'aquestes instantànies.

## Conseqüències

- Podem reprocessar-ho tot si canvien les regles de neteja.
- Comparant instantànies detectarem altes, baixes i modificacions (Fase 2).
- El volum és petit (uns quants milers de files), així que descarregar-ho tot és barat.
- Els noms de columna de l'API es mapegen a partir del nom visible a les metadades,
  i el sistema avisa si l'esquema canvia.

# 0001 · Ingesta en instantáneas crudas e inmutables

**Estado:** aceptada

## Contexto

El dataset se actualiza de forma periódica y los registros existentes pueden corregirse o
eliminarse. La API no ofrece un historial de cambios.

## Decisión

Cada ingesta descarga el dataset completo vía API SODA y lo guarda sin modificar en
`data/raw/<timestamp>/`, junto con los metadatos del portal y un manifiesto con el hash.
Toda la limpieza se hace después, a partir de estas instantáneas.

## Consecuencias

- Podemos reprocesar todo si cambian las reglas de limpieza.
- Comparando instantáneas detectaremos altas, bajas y modificaciones (Fase 2).
- El volumen es pequeño (unos pocos miles de filas), así que descargar todo es barato.
- Los nombres de columna de la API se mapean a partir del nombre visible en los metadatos,
  y el sistema avisa si el esquema cambia.

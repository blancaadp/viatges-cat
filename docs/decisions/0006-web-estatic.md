# 0006 · Web estàtic generat amb Python i desplegat a Vercel

**Estat:** acceptada

## Context

contractes-cat fa servir Next.js a Vercel i consulta l'API de Socrata en directe, perquè
el seu dataset té milions de registres. El nostre té uns 1.500 viatges, canvia un cop per
setmana i el valor afegit (exclusió p99, destinacions normalitzades, duplicats, retard de
publicació) només existeix a la nostra base de dades, no a Socrata.

## Decisió

1. **Web estàtic.** Cada execució genera tot el web a `site/` amb `viatges web`: HTML,
   CSS, JS i les dades en JSON i CSV. No hi ha servidor ni cap token al navegador.
2. **Generat amb Python i Jinja2**, no amb un framework de JavaScript: el projecte ja és
   Python i així no cal Node ni al local ni al workflow.
3. **Gràfics en SVG generats al servidor**, que es veuen sense JavaScript. El JavaScript
   només afegeix el tooltip i l'explorador (filtres, ordenació, paginació i exportació a CSV
   al navegador, sobre `dades/viatges.json`, uns 400 KB).
4. **Una pàgina per viatge** (`viatge/<id>/`), perquè cada registre tingui una adreça que
   es pugui compartir i indexar.
5. **Xifres:** compten tots els viatges excepte els exclosos per durada (p99, ADR 0004) i els
   duplicats. Ho explica la pàgina de metodologia.
6. **Publicació:** el workflow `web.yml` reconstrueix la base de dades des de Turso,
   genera el web i el desplega a Vercel (CLI en format «prebuilt», amb la carpeta `site/`).
   El web es construeix a GitHub Actions i no a Vercel, perquè necessita les dades de Turso.
   **Només s'executa a mà** (revisió 2026-10-20): els canvis es revisen en local i es
   publiquen quan es decideix, en lloc de desplegar a cada push o cada dilluns.

## Conseqüències

- Primera versió: inici, explorador, fitxa de viatge i metodologia. Les pàgines de
  persones, destinacions i retard de publicació es poden afegir sense canviar
  l'arquitectura.
- Vercel serveix el web des de l'arrel (`--base "/"`), de manera que no cal cap camí base.
  El desplegament s'activa amb la variable `PUBLICAR_WEB` i els secrets `VERCEL_TOKEN`,
  `VERCEL_ORG_ID` i `VERCEL_PROJECT_ID`; sense això, el web queda com a artefacte de cada
  execució. Funciona amb el repositori privat.
- Si en el futur volem consultes en directe o una API, Turso ja té les dades.

# 0006 · Web estàtic generat amb Python i publicat a GitHub Pages

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
   genera el web i el publica a GitHub Pages després de cada actualització setmanal i de
   cada canvi al codi.

## Conseqüències

- Primera versió: inici, explorador, fitxa de viatge i metodologia. Les pàgines de
  persones, destinacions i retard de publicació es poden afegir sense canviar
  l'arquitectura.
- GitHub Pages en un repositori privat requereix un pla de pagament de GitHub. Amb el pla
  gratuït, el repositori ha de ser públic. Mentre és privat, el web es genera igualment i
  queda com a artefacte de cada execució; la publicació s'activa amb la variable
  `PUBLICAR_WEB`.
- Si en el futur volem consultes en directe o una API, Turso ja té les dades.

# 0005 · Automatització setmanal i còpia a Turso

**Estat:** acceptada

## Context

Fins ara les instantànies només eren en local (`data/raw/`, exclosa de git). Si s'executa
la ingesta a GitHub Actions, cada execució comença amb una màquina buida: cal un lloc
persistent per a l'historial. Com fa contractes-cat, volem una còpia en una base de dades
allotjada, consultable després des del web (Fase 4).

## Decisió

1. **Turso** (libSQL, compatible amb SQLite) és la base de dades allotjada. La nostra base de
   dades local ja és SQLite, així que les taules es copien tal com són. Hi accedim per
   l'API HTTP de Turso amb `httpx`, sense dependències noves.
2. **Turso guarda també les instantànies en cru**, i no només les taules derivades:
   - `arxiu_instantanies`: una fila per instantània (manifest i metadades en JSON).
   - `arxiu_files`: una fila per registre i instantània, amb el JSON original i l'ordre.
   Aquestes dues taules només creixen. Amb elles es pot reconstruir `data/raw/` byte a byte
   (`viatges pull` en comprova el hash) i, per tant, tot el que en deriva.
3. **Les taules derivades** (`instantanies`, `viatges`, `trams`, `canvis`, `historial_ids`)
   es reemplacen senceres a cada `viatges push`, dins d'una transacció, a partir de
   `data/viatges.sqlite`.
4. **Una instantània idèntica a l'anterior no es desa.** Si el hash de les files coincideix,
   `viatges update` l'esborra. Així no s'omple l'arxiu de còpies iguals setmana rere setmana.
5. **GitHub Actions** (`.github/workflows/actualitzacio.yml`) s'executa cada dilluns i també
   a mà: `pull` → `update` → `push`, i fa commit dels informes (`reports/`) al repositori.

## Conseqüències

- Secrets necessaris a GitHub: `TURSO_URL`, `TURSO_TOKEN` (lectura i escriptura),
  `SODA_APP_TOKEN` i `SODA_APP_SECRET`.
- Per al web caldrà un token de **només lectura** diferent.
- Volum estimat: ~1,6 MB per instantània nova; amb canvis cada setmana, menys de 100 MB
  l'any, dins del pla gratuït de Turso.
- Per treballar en local amb tot l'historial: `viatges pull` abans de qualsevol altra ordre.

# Konténerizált környezet auditja – CIS Docker Benchmark

IT Audit tantárgy, páros projekt.

**Téma:** Konténerizált környezetben futó webalkalmazás (időpontfoglaló rendszer) auditja a CIS Docker Benchmark alapján.

| Szerep | Személy | Feladat |
|---|---|---|
| Auditor (vezető auditor) | _TBD_ | audit terv, bizonyítékgyűjtés, kockázatértékelés, jelentés |
| Auditált / rendszergazda | _TBD_ | alkalmazás, konténerek, VM üzemeltetése, javítások |

## Leadandók

- Dokumentáció (audit terv + bizonyítékok + jelentés), **max. 20 oldal**
- Prezentáció, **max. 10 dia**
- Bemutatás

## Repó felépítése

```
app/                         Az időpontfoglaló alkalmazás (Flask) – v1-ben és v2-ben azonos
docs/
  jelentes.md / .docx        Audit jelentés (terv + bizonyítékok + jelentés)
  prezentacio.pptx           Prezentáció
  attekintes.html            Interaktív áttekintés (böngészőben nyitható)
  audit-terv.md              Audit terv (a jelentés 2. fejezetének alapja)
  templates/
    megallapitas-sablon.md   Egy megállapítás (finding) leírása
    interju-jegyzokonyv.md   Interjú jegyzőkönyv a rendszergazdával
infra/
  README.md                  A vizsgált környezet specifikációja (v1 naiv, v2 hardened)
  v1/                        A kiinduló („naiv”) telepítés: compose, Dockerfile-ok, app
  v2/                        A javított telepítés (az akcióterv után)
scripts/
  setup-host.sh              A host előkészítése (Ubuntu vagy Manjaro/Arch)
  enable-apparmor-grub.sh    AppArmor bekapcsolása (kernel boot paraméter)
  collect-evidence.sh        Bizonyítékgyűjtés: docker-bench, Trivy, konfigurációk + hash
  deploy-v2.sh               A v2 telepítése
  functional-test.sh         A v2 funkcionális tesztje
evidence/
  README.md                  Bizonyítékkezelési szabályok
  <futás-azonosító>/         Egy-egy mérés nyers kimenetei (pl. 2026-11-08T1402Z_v1/)
pptk/                        Az előadások anyaga (referencia)
```

## Állapot

Az audit elkészült (2026-11-08):

- Leadandó dokumentáció: [docs/jelentes.docx](docs/jelentes.docx) (14 oldal; forrás: [docs/jelentes.md](docs/jelentes.md))
- Prezentáció: [docs/prezentacio.pptx](docs/prezentacio.pptx) (10 dia, előadói jegyzetekkel)
- Interaktív áttekintés: [docs/attekintes.html](docs/attekintes.html) (böngészőben megnyitható)
- Bizonyítékok: `evidence/2026-11-08T1402Z_v1` (v1), `evidence/2026-11-08T1406Z_v2` (v2), `evidence/2026-11-08T1409Z_v2-functional` (v2 funkcionális teszt), `evidence/2026-11-08T1424Z_v2-dash` (a docker-bench dash-hibájának bizonyítéka)
- Eredmény: docker-bench score 5 → 61, WARN 29 → 4, magas + kritikus CVE 454 → 41

Újragenerálás (a `docx` és a `pptxgenjs` npm csomag kell hozzá):

```bash
NODE_PATH=<node_modules> node scripts/build-report.js
NODE_PATH=<node_modules> node scripts/build-slides.js [<pptx skill>/scripts/apply_theme.js]
python3 scripts/summarize.py evidence/2026-11-08T1402Z_v1 evidence/2026-11-08T1406Z_v2
```

## Menet

1. Audit terv véglegesítése és jóváhagyása (`docs/audit-terv.md`)
2. v1 környezet telepítése a Linux VM-en (`infra/v1`)
3. Első mérés: `sudo ./scripts/collect-evidence.sh v1`
4. Megállapítások és kockázatértékelés, akcióterv
5. Javítás (`infra/v2`)
6. Újramérés (utókövetés): `sudo ./scripts/collect-evidence.sh v2`
7. Jelentés és prezentáció

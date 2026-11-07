# Bizonyítékkezelés

> „Minden, ami alátámasztja a jelentést!” (04 – IT Audit dokumentáció)

## Szabályok

1. **Egy mérés, egy könyvtár:** `evidence/<UTC időbélyeg>_<címke>/`, pl. `2026-11-20T1430Z_v1/`. A könyvtárat a `scripts/collect-evidence.sh` hozza létre, és meglévőt nem ír felül.
2. **A nyers kimenet érinthetetlen.** Az elemzés, a megjegyzések és a kivágatok a `docs/` alá kerülnek, a nyers fájlra hivatkozva (fájlnév + sor).
3. **Integritás:** minden mérési könyvtárban van egy `SHA256SUMS`. Ellenőrzés:
   ```bash
   cd evidence/<futás> && sha256sum -c SHA256SUMS
   ```
   A mérés után azonnal commitolni kell. A git commit hash és az időbélyeg együtt igazolja a bizonyíték keletkezési idejét.
4. **Titkok:** a `docker inspect` kimenetben a jelszó-, kulcs- és token-jellegű környezeti változók értékét a szkript maszkolja. Ha más fájlban is titok kerül elő, akkor azt a hash készítése *előtt* kell maszkolni, és a `meta/run.log` fájlba be kell írni.
5. **Mérési napló:** `meta/run.log` – ki, mikor, milyen parancsokat futtatott, és milyen hibák történtek.

## Egy mérés tartalma

| Könyvtár | Tartalom | Audit módszer |
|---|---|---|
| `meta/` | host, Docker- és eszközverziók, futási napló | – |
| `config/` | `daemon.json`, auditd szabályok, systemd unitok, jogosultságok, compose és Dockerfile másolatok | dokumentumvizsgálat |
| `docker/` | `ps`, `images`, `inspect` (konténer, hálózat) | megfigyelés |
| `docker-bench/` | `docker-bench.log`, `docker-bench.log.json` | automatizált tesztelés (CIS) |
| `trivy/` | image CVE-k (JSON + HIGH/CRITICAL tábla), konfigurációs hibák | automatizált tesztelés |

Az interjú jegyzőkönyve a `docs/` alá kerül ([sablon](../docs/templates/interju-jegyzokonyv.md)).

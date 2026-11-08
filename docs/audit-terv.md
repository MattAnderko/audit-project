# Audit terv

**Az audit címe:** Konténerizált webalkalmazás-környezet megfelelőségi auditja a CIS Docker Benchmark alapján
**Verzió:** 1.0 · **Dátum:** 2026-11-07 · **Jóváhagyta:** _TBD (megbízó / oktató)_

> A fejezetek az előadás audit terv elemeit követik (04 – IT Audit dokumentáció, „A tervezés” és „Tervezés dokumentumai” diák).
> A `_TBD_` jelölésű részeket a felek egyeztetése után kell kitölteni.

---

## 1. Az audit célja és a jelentés címzettjei

**Cél:** Független, technikai eszközökkel alátámasztott értékelést adni arról, hogy a vizsgált konténerizált környezet (Docker host, Docker daemon, konténer image-ek és futó konténerek) konfigurációja mennyiben felel meg a CIS Docker Benchmark ajánlásainak. Emellett:

- azonosítani az eltéréseket, és kockázatot rendelni hozzájuk,
- javaslatot tenni a kezelésükre (akcióterv),
- a javítások után újraméréssel (utókövetés) igazolni a javítások eredményességét.

**A jelentés címzettjei:**
- a rendszer üzemeltetője (auditált fél),
- a megbízó: a tantárgy oktatója.

**Az audit típusa:** belső jellegű, megfelelőségi (standardnak való megfelelés) audit, technikai tesztelés alapján (02 – IT Audit típusok).

## 2. Az audit tárgya

**A vizsgált rendszer:** egy időpontfoglaló webalkalmazás és az azt futtató környezet.

| Réteg | Komponens | Megjegyzés |
|---|---|---|
| Host | Manjaro Linux, natív telepítés (kernel 6.18.33) | AppArmor és auditd aktív |
| Konténer-platform | Docker Engine 29.8.2, Docker Compose v5.1.0 | |
| Konténerek | `proxy` – Nginx reverse proxy | egyedüli publikált port |
| | `app` – időpontfoglaló webalkalmazás (Python, Flask, gunicorn) | belső hálózat |
| | `db` – PostgreSQL | belső hálózat, perzisztens volume |
| Build | Dockerfile-ok, `compose.yaml`, `daemon.json` | dokumentumvizsgálat tárgya |

A részletes leírás az [infra/README.md](../infra/README.md) fájlban található. A jelentés tartalmaz majd egy architektúra-ábrát is.

### 2.1 Kizárások

| Kizárt terület | Indoklás |
|---|---|
| CIS Docker Benchmark 7. fejezet (Docker Swarm) | A környezet nem használ Swarm módot, ezért nem alkalmazható (N/A). |
| Az alkalmazás forráskódjának biztonsági vizsgálata (SAST, OWASP ASVS / Top 10, DAST) | Az audit a futtatókörnyezetre irányul, az alkalmazásszintű vizsgálat külön audit tárgya lehet. |
| A hypervisor és a fizikai infrastruktúra | Nem része a vizsgált rendszernek. |
| Szervezeti és HR kontrollok, üzletmenet-folytonosság (BCP/DRP) | Oktatási környezetben nem értelmezhető. A mentés megléte technikai szinten érintett. |
| Behatolásteszt, aktív támadás | Nem része a megbízásnak. |

> **Teljeskörűség (04. előadás):** a tárgy minden rétegre (host, daemon, image, runtime) kiterjed, nem csak az alkalmazásra.

## 3. A vizsgálat alapja (követelményrendszer)

| Követelmény | Verzió | Szerep |
|---|---|---|
| **CIS Docker Benchmark** | v1.6.0 (a docker-bench-security `154869d` ezt implementálja) | elsődleges mérce |
| CIS 4.x „image-ek szkennelése és újraépítése” ajánlás, Trivy-vel mérve | – | kiegészítő bizonyíték az image-sérülékenységekhez |
| NIST Cybersecurity Framework | 1.1 / 2.0 | a megállapítások besorolása (PR.AC, PR.DS, PR.IP, DE.CM, …) |

**A CIS Docker Benchmark fejezetei:**

| # | Fejezet | Vizsgálva |
|---|---|---|
| 1 | Host Configuration | igen |
| 2 | Docker Daemon Configuration | igen |
| 3 | Docker Daemon Configuration Files | igen |
| 4 | Container Images and Build File Configuration | igen |
| 5 | Container Runtime Configuration | igen |
| 6 | Docker Security Operations | igen (részben manuális) |
| 7 | Docker Swarm Configuration | nem (N/A) |

**Értékelési szempont:** a CIS ajánlások *Level 1* profilját tekintjük elvárt szintnek. A *Level 2* ajánlásokat informatív jelleggel közöljük.

## 4. Auditorok és szerepköreik, függetlenség

| Név | Szerep | Felelősség |
|---|---|---|
| Anderko Máté | Vezető auditor | tervezés, bizonyítékgyűjtés és -kezelés, értékelés, jelentés |
| _TBD_ | Auditált fél / rendszergazda (közreműködő) | hozzáférés biztosítása, interjú, dokumentáció átadása, javítások végrehajtása |

**Függetlenségi nyilatkozat:**
Az auditor nem vett részt a vizsgált rendszer tervezésében, telepítésében és konfigurálásában, saját munkáját nem vizsgálja (01. előadás, „Nem vizsgálhatja önmagát!”). Az audit oktatási célú, ezért a két fél egy csapat tagja. Ezt a jelentés a korlátok között rögzíti.

**Titoktartás:** az audit során megszerzett adatok (pl. jelszavak, kulcsok) nem kerülnek a jelentésbe. A bizonyítékokban ezeket maszkolni kell.

## 5. Résztvevők és a vizsgált fél kötelezettségei

- Az auditor részére hozzáférést kell biztosítani a vizsgált hosthoz (sudo jogosultságú, naplózott felhasználó).
- Át kell adni minden, a tárgyhoz kapcsolódó dokumentumot: Dockerfile-ok, `compose.yaml`, `daemon.json`, telepítési leírás.
- Az audit ideje alatt (a bizonyítékgyűjtés két mérési pontja között) a konfigurációt nem lehet változtatni. A javítás csak az első jelentés után történhet.
- A rendszergazda nyilatkozik az átadott információk valódiságáról és teljességéről (*representation letter*, 04. előadás).

## 6. Előzetes információk

_TBD – a kick-off után kitöltendő:_ a rendszer célja és felhasználói köre, a kezelt adatok (név, e-mail, időpont: személyes adat!), a hozzáférési útvonalak, valamint az ismert eltérések és felvállalt kockázatok.

## 7. Módszertan

| Módszer (01., 04. előadás) | Alkalmazás ebben az auditban | Bizonyíték |
|---|---|---|
| Dokumentumvizsgálat (inspection) | Dockerfile-ok, `compose.yaml`, `daemon.json`, auditd szabályok átnézése | másolat, hash |
| Interjú, érdeklődés és megerősítés | Strukturált interjú a rendszergazdával (frissítési gyakorlat, mentés, jogosultságok, titkok kezelése) | jegyzőkönyv ([sablon](templates/interju-jegyzokonyv.md)) |
| Automatizált tesztelés | **docker-bench-security** (CIS 1–6. fejezet), **Trivy** (`image`: CVE-k, `config`: hibás beállítások) | nyers kimenet (log, JSON) |
| Megfigyelés (observation) | `docker inspect`, `docker info`, futó konténerek és hálózatok lekérdezése | nyers kimenet |
| Újrateljesítés | A mérés megismétlése a javítások után, azonos eszközzel és beállítással | második mérés kimenete |

**Az eszközök:**

| Eszköz | Verzió | Cél |
|---|---|---|
| docker-bench-security | commit `154869d` (2026-06-04) | CIS Docker Benchmark automatizált ellenőrzése |
| Trivy | 0.75.0 | image-sérülékenységek, Dockerfile és compose misconfiguration |
| (opcionális) Hadolint | _TBD_ | Dockerfile best practice |

> Az automatizált eszköz eredménye önmagában nem megállapítás. Minden FAIL / WARN eredményt az auditor manuálisan ellenőriz (a fals pozitívokat kiszűri), és a manuális (*Manual*) CIS ajánlásokat külön értékeli.

### 7.1 Kockázatértékelés módszere

A 07. előadás alapján a kockázat a **hatás** és a **bekövetkezési valószínűség** függvénye, háromszintű skálán:

| Hatás \ Valószínűség | Alacsony | Közepes | Magas |
|---|---|---|---|
| **Magas** | Közepes | Magas | Kritikus |
| **Közepes** | Alacsony | Közepes | Magas |
| **Alacsony** | Alacsony | Alacsony | Közepes |

- **Hatás:** a bizalmasság, sértetlenség vagy rendelkezésre állás sérülésének mértéke (pl. konténerkitörés esetén host-szintű kompromittálódás).
- **Valószínűség:** kihasználhatóság (pl. hálózatról elérhető-e, ismert-e publikus exploit), előfeltételek.

**Kockázatkezelési módok:** javítás (akcióterv alapján), felvállalás (indoklással), áthárítás.

Minden javasolt intézkedés besorolásra kerül a **kontrolltípus** szerint (09. előadás: preventív, felismerő, hatáscsökkentő, helyreállító), illetve a **NIST CSF** kategóriához.

## 8. Bizonyítékkezelés

- Minden mérés egy azonosítóval ellátott könyvtárba kerül (`evidence/<dátum>_<v1|v2>/`).
- Minden fájlhoz SHA-256 hash készül (`SHA256SUMS`), a mérés időpontja és az eszközverziók rögzítésre kerülnek.
- A nyers kimenetek nem módosíthatók. Az elemzés külön fájlban készül.
- A titkokat (jelszavak, tokenek) tartalmazó kimeneteket a hash készítése előtt maszkolni kell, és ezt a mérési naplóban jelezni kell.

Részletek: [evidence/README.md](../evidence/README.md).

## 9. Időbeosztás

| Fázis | Tevékenység | Felelős | Időpont |
|---|---|---|---|
| Tervezés | Audit terv, kick-off, előzetes információk | auditor | _TBD_ |
| Előkészítés | v1 környezet telepítése, dokumentáció átadása | rendszergazda | _TBD_ |
| Lebonyolítás I. | Első mérés, dokumentumvizsgálat, interjú | auditor | _TBD_ |
| Értékelés | Megállapítások, kockázatértékelés, köztes jelentés | auditor | _TBD_ |
| Javítás | Akcióterv végrehajtása (v2) | rendszergazda | _TBD_ |
| Utókövetés | Újramérés, összehasonlítás | auditor | _TBD_ |
| Jelentés | Végleges jelentés, prezentáció | közös | _TBD_ |
| Bemutatás | Prezentáció | közös | _TBD_ |

## 10. Az audit kimenetei

1. Audit terv (ez a dokumentum)
2. Bizonyítékok (nyers kimenetek, interjú jegyzőkönyv, konfigurációs másolatok)
3. Köztes jelentés a megállapításokkal (az akcióterv alapja)
4. Végleges audit jelentés: összefoglalás, elvégzett elemzések, korlátok, megállapítások kockázattal, javaslatok, utókövetés eredménye (04. előadás, „Jelentés tartalma”)
5. Prezentáció

## 11. Korlátok

- Az audit egy adott időpontra vonatkozik (pillanatkép), nem a működés hatékonyságát vizsgálja egy időszakon át.
- Oktatási környezet: a felek függetlensége korlátozott. A rendszer nem éles, és nincsenek valódi felhasználói adatai.
- Az automatizált eszközök lefedettsége nem teljes. A manuális ajánlások értékelése az auditor szakmai megítélésén alapul.

# Konténerizált webalkalmazás-környezet megfelelőségi auditja a CIS Docker Benchmark alapján

Audit dokumentáció: audit terv, bizonyítékok és audit jelentés

| | |
|---|---|
| **Tantárgy** | IT Audit – páros audit projekt |
| **Vezető auditor** | Anderko Máté |
| **Auditált fél / rendszergazda** | _TBD_ |
| **A vizsgált rendszer** | „Időpontfoglaló” webalkalmazás és Docker futtatókörnyezete |
| **Követelményrendszer** | CIS Docker Benchmark v1.6.0 |
| **Mérési időpontok** | v1: 2026-11-07 15:42 UTC · v2 (utókövetés): 2026-11-07 15:52 UTC |
| **Dokumentum verzió** | 1.0 |

# 1. Vezetői összefoglaló

Az audit célja annak értékelése volt, hogy egy időpontfoglaló webalkalmazást futtató, három konténerből (Nginx reverse proxy, Python webalkalmazás, PostgreSQL) álló Docker környezet konfigurációja mennyiben felel meg a **CIS Docker Benchmark v1.6.0** ajánlásainak. A vizsgálat technikai eszközökkel (docker-bench-security, Trivy) és dokumentumvizsgálattal történt. Az első mérés után akcióterv készült, majd a javítások után újramérés (utókövetés).

**Főbb eredmények:**

- A kiinduló (v1), tipikus alapbeállításokkal telepített környezetben **14 megállapítást** tettünk, ebből **1 kritikus, 4 magas, 4 közepes és 5 alacsony** kockázatú. A legsúlyosabb: az adatbázis-szerver gyenge, a konfigurációs fájlban nyílt szövegként tárolt jelszóval, a host **minden hálózati interfészén elérhető** volt (M-05).
- A konténerek root felhasználóval futottak, a jelszavak a `docker inspect` kimenetéből kiolvashatók voltak, és a nem rögzített (`latest`) alap image-ekben **448 magas vagy kritikus** súlyosságú ismert sérülékenység volt.
- Az akcióterv végrehajtása után a docker-bench pontszáma **5-ről 38-ra** nőtt. A WARN eredmények száma **33-ról 18-ra** csökkent, a magas és kritikus sérülékenységeké **448-ról 41-re** (−91%). **9 megállapítás teljesen, 1 részben javult**, 2 a platform korlátai miatt nyitott maradt, 2-t tudatosan felvállaltunk. A kritikus és a magas kockázatú megállapítások mind megszűntek vagy csökkentek.
- A fennmaradó eltérések jellemzően **a vizsgálati platform korlátai** (a WSL2 kernel nem támogatja az auditd-t és az AppArmort), **tudatosan felvállalt kockázatok** (pl. authorization plugin), illetve az upstream image-ekben maradt, már javítható sérülékenységek. Ez utóbbiakra új akciótervi pontot javaslunk.
- Az automatizált eszköz **öt ellenőrzésnél adott téves eredményt** (két hamis negatív, két hamis pozitív, egy csak formálisan teljesülő). Ez megerősíti, hogy az eszköz kimenete auditori ellenőrzés nélkül nem fogadható el.

**Összegzés:** a v2 környezet konfigurációja a CIS Docker Benchmark Level 1 ajánlásainak a vizsgált platformon megvalósítható részét lényegében teljesíti. Az éles üzembe helyezés előtt az M-01 (host-auditálás), az M-12 (AppArmor) és a maradék sérülékenységek kezelése szükséges egy teljes értékű Linux hoston.

# 2. Audit terv

A terv az előadásokon bemutatott audit terv elemeit követi (cél, tárgy, vizsgálati alap, auditorok, résztvevők, előzetes információk, módszertan, időbeosztás). A teljes, önálló terv a repó `docs/audit-terv.md` fájljában található. Itt a lényeges elemeket foglaljuk össze.

## 2.1 Az audit célja és típusa

**Cél:** független, technikai eszközökkel alátámasztott értékelést adni a vizsgált konténerizált környezet (Docker host, Docker daemon, image-ek, futó konténerek) CIS Docker Benchmarknak való megfeleléséről. Emellett azonosítani az eltéréseket, kockázatot rendelni hozzájuk, akciótervet javasolni, és újraméréssel igazolni a javítások eredményességét.

**Típus:** belső jellegű megfelelőségi audit (standardnak való megfelelés), technikai tesztelésen alapulva. **A jelentés címzettjei:** a rendszer üzemeltetője és a megbízó (a tantárgy oktatója).

## 2.2 Az audit tárgya és kizárások

| Réteg | Komponens | Verzió (v1) |
|---|---|---|
| Host | Ubuntu 24.04.5 LTS, WSL2 kernel 6.18 | – |
| Konténer-platform | Docker Engine (docker-ce), Compose v2 | 29.9.3 |
| Konténer: proxy | Nginx reverse proxy | nginx:latest (1.31.8) |
| Konténer: app | Időpontfoglaló (Python, Flask, gunicorn) | python:latest (3.15.2) |
| Konténer: db | PostgreSQL | postgres:latest (18.6) |
| Build / konfiguráció | Dockerfile, compose.yaml, daemon.json | – |

| Kizárt terület | Indoklás |
|---|---|
| CIS 7. fejezet (Swarm) | A környezet nem használ Swarm módot (N/A). |
| Az alkalmazás forráskódja (SAST, OWASP ASVS, DAST) | Az audit a futtatókörnyezetre irányul. |
| Hypervisor, fizikai infrastruktúra | Nem része a vizsgált rendszernek. |
| Szervezeti kontrollok, BCP/DRP | Oktatási környezetben nem értelmezhető. |
| Behatolásteszt | Nem része a megbízásnak. |

A **teljeskörűség** érdekében a tárgy minden rétegre kiterjedt (host, daemon, daemon-fájlok, image-ek, runtime), nem csak az alkalmazásra.

## 2.3 A vizsgálat alapja

Elsődleges mérce a **CIS Docker Benchmark v1.6.0**. Ezt a verziót implementálja a docker-bench-security használt változata (commit `154869d`). Elvárt szint a *Level 1* profil. Kiegészítő bizonyítékként a CIS 4.4 („images are scanned and rebuilt to include security patches”) ajánláshoz a **Trivy** sérülékenység- és konfigurációs szkennelését használtuk. A megállapításokat a **NIST Cybersecurity Framework** kategóriáihoz is hozzárendeltük.

## 2.4 Auditorok, résztvevők, függetlenség

| Szerep | Személy | Felelősség |
|---|---|---|
| Vezető auditor | Anderko Máté | tervezés, bizonyítékgyűjtés és -kezelés, értékelés, jelentés |
| Auditált fél / rendszergazda | _TBD_ | hozzáférés, dokumentáció átadása, javítások végrehajtása |

**Függetlenség:** az auditor saját munkáját nem vizsgálja. Mivel azonban oktatási projektről van szó, a két fél egy csapat tagja, ezért a függetlenség korlátozott (lásd 8. fejezet). **Titoktartás:** a jelszavak a bizonyítékokban maszkolva szerepelnek, a v2 titkai pedig nem kerültek a repóba.

**A vizsgált fél kötelezettségei:** sudo jogú hozzáférés biztosítása, a konfigurációs fájlok átadása, valamint a konfiguráció változatlanul hagyása a két mérési pont között. A javítás csak a köztes jelentés után kezdődhetett.

## 2.5 Módszertan

| Módszer | Alkalmazás | Bizonyíték |
|---|---|---|
| Dokumentumvizsgálat | Dockerfile, compose.yaml, daemon.json, systemd unitok, auditd szabályok | `config/` másolatok |
| Megfigyelés | `docker inspect`, `docker ps`, hálózatok, mount-pontok | `docker/` kimenetek |
| Automatizált tesztelés | docker-bench-security (CIS 1–7.), Trivy image és config | `docker-bench/`, `trivy/` |
| Manuális ellenőrzés | Minden WARN és PASS eredmény szúrópróbás ellenőrzése, eszköz-forráskód vizsgálata | elemzés (5.1–5.2 fejezet) |
| Újrateljesítés | Ugyanazon mérés megismétlése a javítások után | v2 mérés |

**Kockázatértékelés:** a kockázat a hatás és a bekövetkezési valószínűség függvénye, háromszintű skálán. A hatás a bizalmasság, a sértetlenség és a rendelkezésre állás sérülését jelenti, a valószínűség a kihasználhatóságot (hálózati elérhetőség, előfeltételek). A kezelési módok: **javítás**, **felvállalás** vagy **áthárítás**.

| Hatás \ Valószínűség | Alacsony | Közepes | Magas |
|---|---|---|---|
| **Magas** | Közepes | Magas | Kritikus |
| **Közepes** | Alacsony | Közepes | Magas |
| **Alacsony** | Alacsony | Alacsony | Közepes |

## 2.6 Időbeosztás

| Fázis | Tevékenység | Eredmény |
|---|---|---|
| Tervezés | Audit terv, tárgy és kizárások rögzítése | `docs/audit-terv.md` |
| Előkészítés | Host és v1 környezet telepítése (`scripts/setup-host.sh`, `infra/v1`) | futó v1 |
| Lebonyolítás I. | Első mérés, dokumentumvizsgálat | `evidence/2026-11-07T1542Z_v1` |
| Értékelés | Megállapítások, kockázatértékelés, akcióterv | 6. fejezet |
| Javítás | v2 környezet (`scripts/deploy-v2.sh`, `infra/v2`) | futó v2 |
| Utókövetés | Újramérés, összehasonlítás | `evidence/2026-11-07T1552Z_v2` |
| Jelentés | Jelen dokumentum, prezentáció | – |

# 3. A vizsgált rendszer

Az alkalmazás egy minimális CRUD webalkalmazás: időpontok listázása, foglalás (név, e-mail, időpont) és egy basic auth-tal védett admin nézet. **Személyes adatot (név, e-mail) kezel.** Az alkalmazás kódja mindkét változatban azonos, csak a futtatókörnyezet változott.

**Architektúra (v1):** a három konténer egyetlen alapértelmezett compose-hálózaton osztozott, és mindhárom konténer publikált portot kapott a host összes interfészén: proxy 80, app 8000, db 5432. A jelszavak a `compose.yaml` `environment:` részében szerepeltek.

**Architektúra (v2):** a proxy az egyetlen publikált port (127.0.0.1:8080). Az app a `frontend` és a `backend` hálózaton is jelen van. Az adatbázis csak a belső (`internal: true`) `backend` hálózaton érhető el. A titkok Docker secretként, fájlból érkeznek.

| Jellemző | v1 („naiv”, tipikus tutorial) | v2 (akcióterv után) |
|---|---|---|
| Alap image | `python:latest`, `nginx:latest`, `postgres:latest` | rögzített verzió + digest, alpine |
| Futtató felhasználó | root (mindhárom) | app: 10001, db: postgres (70), proxy: nginx (101) |
| Titkok | env változó, compose fájlban | Docker secret (`/run/secrets`) |
| Publikált portok | 80, 8000, 5432 – `0.0.0.0` | csak 8080 – `127.0.0.1` |
| Hálózat | egy közös | `frontend` + belső `backend` |
| Erőforrás-korlát | nincs | memória, CPU shares, PID-limit |
| Root fájlrendszer | írható | `read_only` + tmpfs |
| Jogosultságok | alapértelmezett capability-k | `cap_drop: ALL`, `no-new-privileges` |
| Healthcheck | nincs | mindhárom image-ben |
| Restart policy | `always` | `on-failure:5` |
| Daemon (daemon.json) | nincs, alapértelmezett | icc, userns-remap, live-restore, userland-proxy, journald |

# 4. Mérési bizonyítékok

## 4.1 Bizonyítékkezelés

A bizonyítékokat a `scripts/collect-evidence.sh` szkript gyűjtötte, mérésenként külön, időbélyeggel ellátott könyvtárba (`evidence/<UTC időbélyeg>_<címke>/`). Meglévő mérést a szkript nem ír felül. Minden mérés tartalmaz egy **`SHA256SUMS`** fájlt, valamint egy mérési naplót (`meta/run.log`) a futtatott parancsokkal és hibákkal. A `docker inspect` kimenetben a jelszó-jellegű környezeti változók értékét a szkript a hash készítése előtt maszkolta. A nyers kimeneteket nem módosítottuk, az elemzést külön végeztük (`scripts/summarize.py`). A bizonyítékok integritása így ellenőrizhető:

`cd evidence/<mérés> && sha256sum -c SHA256SUMS`

| Mérés | Tartalom | Megjegyzés |
|---|---|---|
| `2026-11-07T1542Z_v1` | Kiinduló állapot | elsődleges bizonyíték (v1) |
| `2026-11-07T1549Z_v2` | v2, docker-bench `sh` (dash) alatt | eszközhiba bizonyítéka (5.2 fejezet), értékelésre nem használtuk |
| `2026-11-07T1552Z_v2` | v2, docker-bench `bash` alatt | elsődleges bizonyíték (v2) |

## 4.2 CIS Docker Benchmark – eredmények fejezetenként

A docker-bench 117 ellenőrzést futtatott. Az *INFO* és *NOTE* eredmények manuális értékelést igényelnek, és nem számítanak bele a pontszámba.

| CIS fejezet | PASS v1 | WARN v1 | PASS v2 | WARN v2 |
|---|---|---|---|---|
| 1 Host konfiguráció | 2 | 12 | 1 | 14 |
| 2 Docker daemon konfiguráció | 6 | 7 | 12 | 1 |
| 3 Daemon konfigurációs fájlok | 12 | 0 | 14 | 0 |
| 4 Image-ek és build fájlok | 1 | 3 | 4 | 1 |
| 5 Konténer runtime | 17 | 11 | 26 | 2 |
| 6 Security operations | 0 | 0 | 0 | 0 |
| **Összesen (1–6.)** | **38** | **33** | **57** | **18** |
| docker-bench score | **5** | | **38** | |

A 7. fejezet (Swarm) 9 ellenőrzése N/A, ezért kihagytuk. Az 1. fejezetben a WARN-ok száma a v2-ben nőtt (12 → 14). Az ok: a v2-ben létrejött a `daemon.json`, és ennek auditálását (1.1.11) is ellenőrzi az eszköz, valamint az 1.1.1 v1-es PASS eredménye hamisnak bizonyult (5.2 fejezet).

## 4.3 A v1 mérés főbb bizonyítékai

**Root futtatás (CIS 4.1)** – docker-bench: `running as root: booking-proxy-1 booking-app-1 booking-db-1`. A `docker inspect` kimenetben mindhárom konténernél `Config.User = ""`. A Trivy config szkennelése is jelzi: *DS-0002 (HIGH): Specify at least 1 USER command in Dockerfile*.

**Nyílt titkok (CIS 4.10)** – a `config/compose/compose.yaml` másolatában a jelszavak nyílt szövegként szerepelnek (`POSTGRES_PASSWORD`, `DATABASE_URL`, `ADMIN_PASSWORD`). A `docker inspect` kimenetben ugyanezek a változók megjelennek (a bizonyítékban maszkolva: `***MASKED***`). Így bárki, akinek Docker API hozzáférése van, kiolvashatja őket.

**Publikált portok (CIS 5.9, 5.14)** – docker-bench: `Containers with open ports: booking-proxy-1:80 booking-app-1:8000 booking-db-1:5432`, illetve `port bound to wildcard IP: ...:0.0.0.0`. A `docker/ps.txt` szerint: `0.0.0.0:5432->5432/tcp`.

**Runtime korlátozások hiánya (CIS 5.11–5.13, 5.26, 5.29)** – mindhárom konténer memória-, CPU- és PID-korlát nélkül, írható root fájlrendszerrel és `no-new-privileges` nélkül futott.

**Daemon (CIS 2.x)** – nem létezett `/etc/docker/daemon.json`. WARN eredmény: icc (2.2), userns (2.9), authorization (2.12), naplózás (2.13), no-new-privileges (2.14), live-restore (2.15), userland-proxy (2.16).

**Host auditálás (CIS 1.1.3–1.1.18)** – `auditctl -l` kimenet: *Error sending rule list data request (Operation not permitted)*. A host kernele nem támogatja az audit alrendszert (WSL2).

**Image sérülékenységek (CIS 4.4, Trivy)**:

| Image (v1) | Alap OS | CRITICAL | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|
| booking-app:v1 (python:latest) | Debian 13.7 | 15 | 272 | 709 | 1282 |
| nginx:latest | Debian 13.7 | 1 | 67 | 125 | 164 |
| postgres:latest | Debian 13.7 | 2 | 91 | 162 | 141 |
| **Összesen** | | **18** | **430** | **996** | **1587** |

A 448 magas vagy kritikus sérülékenységből mindössze 39-hez volt javított csomagverzió. A többség a teljes Debian alap image (fordítók, fejlesztői könyvtárak) felesleges csomagjaiból ered (CIS 4.3).

**A `latest` tag rendelkezésre állási kockázata (megfigyelés):** a v1 első buildje sikertelen volt, mert a `python:latest` időközben a **Python 3.15**-re váltott, amelyhez a rögzített `psycopg-binary==3.2.10` csomagnak nem volt bináris változata. A build csak a függőség frissítése után sikerült. Ez gyakorlati példa arra, hogy a nem rögzített alap image egy kódváltozás nélküli újraépítést is eltörhet.

## 4.4 A v2 mérés főbb bizonyítékai

| Image (v2) | Alap OS | CRITICAL | HIGH | Forrás |
|---|---|---|---|---|
| booking-app:v2 | Alpine 3.24.4 | 0 | 5 | a pip vendorolt csomagjai (urllib3, msgpack, setuptools) |
| booking-db:v2 | Alpine 3.24.4 | 1 | 25 | `gosu` Go bináris (Go stdlib 1.24.6) |
| booking-proxy:v2 | Alpine 3.24.2 | 1 | 9 | libexpat, brotli-libs, curl, musl |
| **Összesen** | | **2** | **39** | mind a 41-hez van javított verzió |

A Trivy config szkennelése a v2 Dockerfile-okban **0 hibát** talált (v1: 3). A funkcionális teszt szerint a v2 stack működik (foglalás: HTTP 302, admin: 200, régi jelszóval 401). Az adatbázis port a hostról nem érhető el. Az app konténerben `uid=10001(app)`, a root fájlrendszer írása `Read-only file system` hibát ad, és a környezeti változók között nincs jelszó.

# 5. Elemzés

## 5.1 A docker-bench eredmények auditori ellenőrzése

Minden WARN eredményt összevetettünk a `docker inspect`, a konfigurációs fájlok és a mount-adatok bizonyítékaival. A PASS eredményeket szúrópróbaszerűen ellenőriztük, a gyanús eseteknél az eszköz forráskódja alapján. A manuális (*Manual*, *NOTE*) ajánlásokat külön értékeltük:

| CIS | Ajánlás | v1 értékelés | v2 értékelés |
|---|---|---|---|
| 4.2 | Megbízható alap image | Hivatalos image-ek, de nem rögzített tag | Hivatalos image-ek, digesttel rögzítve |
| 4.3 | Felesleges csomagok | Teljes Debian image, fordítókkal | Alpine, minimális |
| 4.4 | Szkennelés és újraépítés | Nincs folyamat, 448 H+C | Szkennelve, 41 H+C maradt (M-04) |
| 4.8 | setuid/setgid bitek | Nincs eltávolítva | Az app image-ben eltávolítva |
| 4.10 | Titkok a Dockerfile-ban | Nincs a Dockerfile-ban, de a compose-ban igen | Nincs (secret) |
| 5.4 | Capability-k | Alapértelmezett készlet (az eszköz PASS-t ad, mert csak a hozzáadást vizsgálja) | `cap_drop: ALL` |
| 5.9 | Csak a szükséges portok | 3 port, ebből 2 felesleges | 1 port (szükséges, elfogadható) |
| 6.1–6.2 | Image és konténer sprawl | Nem értékelhető (1 projekt) | Nem értékelhető |

## 5.2 Az automatizált eszköz téves eredményei

| # | Ellenőrzés | Eszköz eredménye | Tényleges állapot | Ok (forráskód alapján) |
|---|---|---|---|---|
| T-1 | 2.2, 2.9 (érintett kód: 2.4, 2.5, 2.8, 2.12 is) | WARN (v2, `sh` alatt) | 2.2 és 2.9 megfelel | A szkript bash-szintaxist (`[[ ]]`) használ, de a dokumentáció `sh`-val futtatja. Ubuntun az `sh` a dash, ezért ezek az ágak sosem teljesülnek. **Hamis pozitív.** |
| T-2 | 5.15 Restart policy | PASS (v1) | `restart: always` – nem felel meg | Az ellenőrzés csak `MaximumRetryCount > 5` esetén jelez. Az `always` policy értéke 0, ezért átmegy. **Hamis negatív.** |
| T-3 | 1.1.1 Külön partíció | PASS (v1) | Nincs külön partíció (`findmnt`: `/` → `/dev/sdd`) | A dockerd a gyökérkönyvtárát önmagára bind-mountolja, így a `mountpoint` igazat ad. **Hamis negatív.** |
| T-4 | 5.3 SELinux | PASS (v2) | SELinux nem elérhető (Ubuntu) | Az ellenőrzés csak azt nézi, hogy a `SecurityOpt` nem üres. A `no-new-privileges` ezt formálisan teljesíti. **Formális megfelelés.** |

A T-1 miatt a v2 mérést `bash`-sel megismételtük (`2026-11-07T1552Z_v2`), és a gyűjtőszkriptet javítottuk. A v1 eredményeit a hiba nem befolyásolta: ott nem létezett `daemon.json`, így az érintett ellenőrzések bash alatt is WARN-t adtak volna.

## 5.3 Következtetés az eszközről

Az eszköz kimenete gyors és jól megismételhető, de **önmagában nem bizonyíték a megfelelésre**: 117 ellenőrzésből 5 esetben (2.2, 2.9, 5.15, 1.1.1, 5.3) az eredmény nem tükrözte a valós állapotot, és az 5.4 PASS eredménye is csak a capability-k hozzáadását vizsgálja, az alapértelmezett készletet nem. Az auditban ezért minden megállapítást legalább egy független bizonyítékkal (inspect, konfigurációs fájl, mount-adat) is alátámasztottunk.

# 6. Megállapítások és kockázatértékelés

## 6.1 Megállapítások összesítése

| ID | Megállapítás | CIS | Hatás | Valósz. | Kockázat | NIST CSF |
|---|---|---|---|---|---|---|
| M-05 | Az adatbázis és az app portja minden interfészen publikálva, gyenge jelszóval | 5.9, 5.14, 5.8 | Magas | Magas | **Kritikus** | PR.AC-5 |
| M-02 | A konténerek root felhasználóval futnak | 4.1 | Magas | Közepes | **Magas** | PR.AC-4 |
| M-03 | A jelszavak nyílt szövegként szerepelnek a compose fájlban és a konténer környezetében | 4.10 | Magas | Közepes | **Magas** | PR.DS-1, PR.AC-1 |
| M-04 | Nem rögzített `latest` image-ek, 448 magas/kritikus sérülékenység | 4.2–4.4 | Közepes | Magas | **Magas** | ID.RA-1, PR.IP-12 |
| M-10 | A daemon alapbeállításokkal fut (icc, userns, live-restore, userland-proxy, naplózás) | 2.2, 2.9, 2.13–2.16 | Magas | Közepes | **Magas** | PR.PT-3 |
| M-01 | Nincs auditálás a Docker daemonra és fájljaira | 1.1.3–1.1.18 | Közepes | Közepes | Közepes | DE.CM-3, PR.PT-1 |
| M-06 | Nincs memória-, CPU- és PID-korlát | 5.11, 5.12, 5.29 | Közepes | Közepes | Közepes | PR.DS-4 |
| M-07 | Írható root fájlrendszer | 5.13 | Közepes | Közepes | Közepes | PR.DS-6 |
| M-08 | Nincs `no-new-privileges`, alapértelmezett capability-k | 2.14, 5.26, 5.4 | Közepes | Közepes | Közepes | PR.AC-4 |
| M-12 | Nincs AppArmor profil a konténereken | 5.2 | Közepes | Alacsony | Alacsony | PR.PT-3 |
| M-09 | Nincs HEALTHCHECK | 4.6, 5.27 | Alacsony | Közepes | Alacsony | DE.CM-1 |
| M-11 | `restart: always` policy | 5.15 | Alacsony | Közepes | Alacsony | PR.PT-5 |
| M-13 | Nincs külön partíció a Docker adatainak | 1.1.1 | Közepes | Alacsony | Alacsony | PR.DS-4 |
| M-14 | Nincs authorization plugin és content trust | 2.12, 4.5 | Alacsony | Alacsony | Alacsony | PR.AC-4, PR.DS-6 |

**Megoszlás:** 1 kritikus, 4 magas, 4 közepes, 5 alacsony. Az M-10 a userns-remap hiánya miatt magas: userns nélkül a konténerben futó root UID megegyezik a host root UID-jével, így egy konténerkitörés host szintű kompromittálódást jelent.

## 6.2 A legfontosabb megállapítások részletesen

### M-05 – Felesleges, minden interfészen publikált portok (Kritikus)

**Tény:** a v1-ben a `db` konténer 5432-es és az `app` konténer 8000-es portja a host minden interfészén (`0.0.0.0`) elérhető volt. Az adatbázis jelszava (`booking123`) a compose fájlban nyílt szövegként szerepelt. **Elvárás (CIS 5.9, 5.14):** csak a szükséges portok legyenek nyitva, adott interfészhez kötve. **Kockázat:** a hálózatról közvetlenül elérhető adatbázis gyenge jelszóval a személyes adatok (név, e-mail) teljes kiszivárgását vagy módosítását teszi lehetővé. Az app közvetlen elérése megkerüli a proxy védelmeit. **Javaslat:** csak a proxy publikáljon portot, meghatározott interfészen. Az adatbázis kerüljön belső hálózatra. Kontroll: **preventív**. Kezelés: **javítás**.

### M-02 – Root futtatás (Magas)

**Tény:** mindhárom konténer UID 0-val futott, a Dockerfile-ban nem volt `USER` utasítás. **Kockázat:** egy alkalmazásszintű kódfuttatási sérülékenység esetén a támadó a konténerben root jogot kap, ami a konténerkitörés esélyét és hatását növeli. **Javaslat:** dedikált, nem root felhasználó az image-ben (`USER`). Kontroll: **preventív**. Kezelés: **javítás**.

### M-03 – Nyílt titkok (Magas)

**Tény:** a `POSTGRES_PASSWORD`, `DATABASE_URL` és `ADMIN_PASSWORD` értéke a verziókezelt `compose.yaml`-ban és a konténer környezeti változóiban szerepelt, és a `docker inspect` paranccsal kiolvasható volt. **Kockázat:** a titok a verziókezelőbe, a naplókba és a Docker API-hoz hozzáférő bármely felhasználóhoz eljut. **Javaslat:** Docker secret (fájl alapú, `/run/secrets`), az alkalmazás és a PostgreSQL a `*_FILE` változókon keresztül olvassa. A titkok generálása telepítéskor történjen, és ne kerüljenek a repóba. Kontroll: **preventív**. Kezelés: **javítás**.

### M-04 – Nem rögzített, sérülékeny image-ek (Magas)

**Tény:** `latest` tagek, 18 kritikus és 430 magas súlyosságú sérülékenység. Emellett a `latest` váltása egy build megszakadását okozta (4.3 fejezet). **Kockázat:** ismert sérülékenységek kihasználása, nem reprodukálható build, váratlan üzemzavar. **Javaslat:** rögzített verzió és digest, minimális (alpine) alap image, rendszeres szkennelés és újraépítés. Kontroll: **preventív**. Kezelés: **javítás**.

### M-01 – Hiányzó host-auditálás (Közepes)

**Tény:** nincs auditd szabály a Docker binárisokra és konfigurációs fájlokra. A v2-ben a szabályokat telepítettük (`/etc/audit/rules.d/docker.rules`), de a WSL2 kernel nem támogatja az audit alrendszert (`Operation not permitted`), így a szabályok nem tölthetők be. **Kockázat:** a Docker konfigurációjának jogosulatlan módosítása utólag nem deríthető fel. **Javaslat:** teljes értékű Linux hoston az auditd szabályok betöltése és a naplók központi gyűjtése. Kontroll: **felismerő**. Kezelés: **javítás (platformváltáskor)**, addig **felvállalás**.

# 7. Akcióterv és utókövetés

## 7.1 Akcióterv és végrehajtás

| ID | Intézkedés | Kontroll | Kezelés | v1 | v2 | Állapot |
|---|---|---|---|---|---|---|
| M-05 | Csak a proxy publikál portot, `127.0.0.1:8080`, nem privilegizált port, db a belső hálózaton | preventív | javítás | WARN | PASS | **Javítva** |
| M-02 | `USER` minden image-ben (10001, postgres, 101) | preventív | javítás | WARN | PASS | **Javítva** |
| M-03 | Docker secret, `*_FILE` változók, telepítéskor generált titkok | preventív | javítás | NOTE | megfelel | **Javítva** |
| M-04 | Digesttel rögzített alpine image-ek, Trivy szkennelés | preventív | javítás | 448 H+C | 41 H+C | **Részben** |
| M-10 | `daemon.json`: icc, userns-remap, live-restore, userland-proxy, no-new-privileges, journald | preventív | javítás | 7 WARN | 1 WARN | **Javítva** (2.13 részben) |
| M-06 | `mem_limit`, `cpu_shares`, `pids_limit` | preventív | javítás | WARN | PASS | **Javítva** |
| M-07 | `read_only: true` + tmpfs | preventív | javítás | WARN | PASS | **Javítva** |
| M-08 | `cap_drop: ALL`, `no-new-privileges` | preventív | javítás | WARN | PASS | **Javítva** |
| M-09 | HEALTHCHECK mindhárom image-ben | felismerő | javítás | WARN | PASS | **Javítva** |
| M-11 | `restart: on-failure:5` | hatáscsökkentő | javítás | PASS* | PASS | **Javítva** |
| M-01 | auditd szabályok telepítve | felismerő | javítás / felvállalás | WARN | WARN | **Nyitott** (platformkorlát) |
| M-12 | AppArmor profil | preventív | felvállalás | WARN | WARN | **Nyitott** (platformkorlát) |
| M-13 | Külön partíció `/var/lib/docker` számára | hatáscsökkentő | felvállalás | PASS* | WARN | **Felvállalva** (labor) |
| M-14 | Authorization plugin, content trust | preventív | felvállalás | WARN | WARN | **Felvállalva** |

\* Az eszköz hamis negatív eredménye (5.2 fejezet, T-2 és T-3).

**A felvállalás indoklása:** M-13 – egyetlen, oktatási célú VM, a lemez megtelésének hatása korlátozott. M-14 – a hostot egyetlen adminisztrátor kezeli, a Docker csoportban nincs más felhasználó. A Docker Content Trust (Notary v1) helyett a digest szerinti rögzítés biztosítja az image-ek sértetlenségét (kompenzáló kontroll). A 2.13 a journald miatt formálisan PASS, de távoli naplógyűjtés nincs, ezért csak részben teljesül.

## 7.2 Utókövetés – összehasonlítás

| Mutató | v1 | v2 | Változás |
|---|---|---|---|
| docker-bench score | 5 | 38 | +33 |
| WARN (CIS 1–6.) | 33 | 18 | −45% |
| PASS (CIS 1–6.) | 38 | 57 | +50% |
| Trivy CRITICAL + HIGH | 448 | 41 | −91% |
| Trivy összes sérülékenység | 3137 | 129 | −96% |
| Trivy Dockerfile misconfiguration | 3 | 0 | −100% |
| Publikált portok | 3 (0.0.0.0) | 1 (127.0.0.1) | −2 |
| Root konténerek | 3 | 0 | −3 |

A v2-ben maradt 18 WARN-ból 13 a host-auditálás (M-01), 1 a külön partíció (M-13), 2 az authorization plugin és a content trust (M-14), 1 az AppArmor (M-12). Az 5.9-es WARN az egyetlen, szükséges proxy portra vonatkozik, ez elfogadható.

## 7.3 Új akciótervi javaslatok (maradványkockázat)

| # | Javaslat | Felelős | Prioritás |
|---|---|---|---|
| A-1 | A proxy image-ben `apk upgrade` a build során, vagy újabb alap image (libexpat, brotli, curl) | rendszergazda | magas |
| A-2 | A db image-ből a `gosu` eltávolítása: a konténer eleve `postgres` userrel indul, ezért nincs rá szükség | rendszergazda | magas |
| A-3 | Az app image-ben a pip/setuptools frissítése vagy eltávolítása a futtatási rétegből (multi-stage build) | fejlesztő | közepes |
| A-4 | Telepítés teljes értékű Linux VM-re, auditd és AppArmor engedélyezésével (M-01, M-12) | rendszergazda | közepes |
| A-5 | Rendszeres (pl. heti) Trivy szkennelés és újraépítés CI-ban, a CIS 4.4 folyamatos teljesítéséhez | fejlesztő | közepes |
| A-6 | Távoli naplógyűjtés (journald → központi syslog) a 2.13 teljes teljesítéséhez | rendszergazda | alacsony |

# 8. Korlátok és következtetés

**Korlátok:**

- **Platform:** a vizsgált host WSL2 alatt futó Ubuntu volt. Ez valódi Linux kernel, de nem támogatja az audit alrendszert és az AppArmort, ezért a CIS 1.1.x és 5.2 ajánlások ezen a platformon nem teljesíthetők.
- **Pillanatkép:** az audit két időpontra vonatkozik. A kontrollok működésének hatékonyságát egy időszakon át nem vizsgálta.
- **Függetlenség:** oktatási projekt, az auditor és az auditált fél egy csapat tagja.
- **Interjú:** az interjú jegyzőkönyv sablonja elkészült (`docs/templates/interju-jegyzokonyv.md`), de a rendszergazdai szerepet a csapat töltötte be. Az interjús kérdéseket ezért dokumentumvizsgálattal és technikai megfigyeléssel váltottuk ki.
- **Eszközök:** az automatizált ellenőrzések lefedettsége és pontossága korlátozott (5.2 fejezet). A manuális ajánlások értékelése az auditor szakmai megítélésén alapul.
- **Tárgy:** az alkalmazás forráskódjának biztonsága nem volt része a vizsgálatnak.

**Következtetés:** a tipikus, tutorial-szintű Docker telepítés a CIS Docker Benchmark ajánlásainak jelentős részét nem teljesíti, és kritikus kockázatot hordoz (nyitott adatbázis-port, root konténerek, nyílt titkok). A javasolt intézkedések nagy része a compose fájl és a Dockerfile-ok néhány sorával, az alkalmazás módosítása nélkül megvalósítható. Az utókövetés igazolta, hogy ezek eredményesek. A fennmaradó kockázatok kezelésére a 7.3 fejezet akcióterve szolgál.

# Melléklet – hivatkozott fájlok

| Fájl | Tartalom |
|---|---|
| `docs/audit-terv.md` | Önálló audit terv |
| `infra/v1/`, `infra/v2/` | A vizsgált konfigurációk (compose, Dockerfile, daemon.json, auditd szabályok) |
| `scripts/setup-host.sh` | A host előkészítése (v1) |
| `scripts/deploy-v2.sh` | A v2 hardening telepítése |
| `scripts/collect-evidence.sh` | Bizonyítékgyűjtés (docker-bench, Trivy, konfigurációk, SHA-256) |
| `scripts/summarize.py` | Eredmények összesítése és összehasonlítása |
| `evidence/*/` | Nyers bizonyítékok, `SHA256SUMS`, mérési napló |

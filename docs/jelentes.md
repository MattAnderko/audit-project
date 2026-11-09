# Konténerizált webalkalmazás-környezet megfelelőségi auditja a CIS Docker Benchmark alapján

Audit dokumentáció: audit terv, bizonyítékok és audit jelentés

| | |
|---|---|
| **Tantárgy** | IT Audit, páros audit projekt |
| **Vezető auditor** | Anderko Máté |
| **Auditált fél / rendszergazda** | _TBD_ |
| **A vizsgált rendszer** | „Időpontfoglaló” webalkalmazás és Docker futtatókörnyezete |
| **Követelményrendszer** | CIS Docker Benchmark v1.6.0 |
| **Mérési időpontok** | v1: 2026-11-08 14:02 UTC · v2 (utókövetés): 2026-11-08 15:14 UTC |
| **Dokumentum verzió** | 1.0 |

# 1. Vezetői összefoglaló

Az audit célja annak értékelése volt, hogy egy időpontfoglaló webalkalmazást futtató, három konténerből (Nginx reverse proxy, Python webalkalmazás, PostgreSQL) álló Docker környezet konfigurációja mennyiben felel meg a CIS Docker Benchmark v1.6.0 ajánlásainak. Technikai eszközökkel (docker-bench-security, Trivy) mértünk, és dokumentumvizsgálatot végeztünk. Az első mérés után akciótervet készítettünk, a javítások után pedig újramértünk (utókövetés).

Főbb eredmények:

- A kiinduló (v1), alapbeállításokkal telepített környezetben 13 megállapítást tettünk: 1 kritikus, 4 magas, 4 közepes és 4 alacsony kockázatút. A legsúlyosabb az M-05: az adatbázis-szerver a host minden hálózati interfészén elérhető volt, gyenge jelszóval, amely nyílt szövegként szerepelt a konfigurációs fájlban.
- A konténerek root felhasználóval futottak, a jelszavak a `docker inspect` kimenetéből kiolvashatók voltak, és a nem rögzített (`latest`) alap image-ekben 454 magas vagy kritikus súlyosságú ismert sérülékenység volt.
- Az akcióterv végrehajtása után a docker-bench pontszáma 5-ről 61-re nőtt, a WARN eredmények száma 29-ről 4-re, a magas és kritikus sérülékenységeké 454-ről 0-ra csökkent. Tizenegy megállapítás javult, kettőt tudatosan felvállaltunk. A kritikus és magas kockázatú megállapítások mindegyike megszűnt.
- A v2-ben maradt 4 WARN közül három tudatosan felvállalt kockázat (külön partíció, authorization plugin, content trust), a negyedik az egyetlen, szükséges proxy portra vonatkozik.
- Az automatizált eszköz négy ellenőrzésnél (2.2, 2.9, 5.15, 5.3) adott a valós állapottól eltérő eredményt, ezért a kimenetét auditori ellenőrzés nélkül nem fogadtuk el.

**Összegzés:** a v2 környezet a CIS Docker Benchmark Level 1 ajánlásait a vizsgált hoston a felvállalt kivételekkel teljesíti. Éles üzembe helyezés előtt a rendszeres image-szkennelés és újraépítés, valamint a távoli naplógyűjtés kiépítése javasolt (7.3 fejezet).

# 2. Audit terv

A terv az előadásokon bemutatott audit terv elemeit követi (cél, tárgy, vizsgálati alap, auditorok, résztvevők, előzetes információk, módszertan, időbeosztás). Ez a fejezet a terv lényeges elemeit foglalja össze.

## 2.1 Az audit célja és típusa

**Cél:** független, technikai eszközökkel alátámasztott értékelést adni a vizsgált konténerizált környezet (Docker host, Docker daemon, image-ek, futó konténerek) CIS Docker Benchmarknak való megfeleléséről. Emellett azonosítani az eltéréseket, kockázatot rendelni hozzájuk, akciótervet javasolni, és újraméréssel igazolni a javítások eredményességét.

**Típus:** belső jellegű megfelelőségi audit (standardnak való megfelelés), technikai tesztelésen alapulva. **A jelentés címzettjei:** a rendszer üzemeltetője és a megbízó (a tantárgy oktatója).

## 2.2 Az audit tárgya és kizárások

| Réteg | Komponens | Verzió (v1) |
|---|---|---|
| Host | Manjaro Linux, natív telepítés, kernel 6.18.33, AppArmor és auditd aktív | - |
| Konténer-platform | Docker Engine, Compose | 29.8.2, Compose v5.1.0 |
| Konténer: proxy | Nginx reverse proxy | nginx:latest (1.31.8) |
| Konténer: app | Időpontfoglaló (Python, Flask, gunicorn) | python:latest (3.15.2) |
| Konténer: db | PostgreSQL | postgres:latest (18.6) |
| Build / konfiguráció | Dockerfile, compose.yaml, daemon.json | - |

| Kizárt terület | Indoklás |
|---|---|
| CIS 7. fejezet (Swarm) | A környezet nem használ Swarm módot (N/A). |
| Az alkalmazás forráskódja (SAST, OWASP ASVS, DAST) | Az audit a futtatókörnyezetre irányul. |
| Hypervisor, fizikai infrastruktúra | Nem része a vizsgált rendszernek. |
| Szervezeti kontrollok, BCP/DRP | Oktatási környezetben nem értelmezhető. |
| Behatolásteszt | Nem része a megbízásnak. |

A teljeskörűség érdekében a tárgy minden rétegre kiterjedt: host, daemon, daemon-fájlok, image-ek és runtime.

## 2.3 A vizsgálat alapja

Elsődleges mérce a CIS Docker Benchmark v1.6.0. Ezt a verziót implementálja a docker-bench-security használt változata (commit `154869d`). Elvárt szint a *Level 1* profil. Kiegészítő bizonyítékként a CIS 4.4 („images are scanned and rebuilt to include security patches”) ajánláshoz a Trivy sérülékenység- és konfigurációs szkennelését használtuk. A megállapításokat a NIST Cybersecurity Framework kategóriáihoz is hozzárendeltük.

## 2.4 Auditorok, résztvevők, függetlenség

| Szerep | Személy | Felelősség |
|---|---|---|
| Vezető auditor | Anderko Máté | tervezés, bizonyítékgyűjtés és -kezelés, értékelés, jelentés |
| Auditált fél / rendszergazda | _TBD_ | hozzáférés, dokumentáció átadása, javítások végrehajtása |

**Függetlenség:** az auditor saját munkáját nem vizsgálja. Mivel azonban oktatási projektről van szó, a két fél egy csapat tagja, ezért a függetlenség korlátozott (lásd 8. fejezet). **Titoktartás:** a jelszavak a bizonyítékokban maszkolva szerepelnek, a v2 titkai pedig nem kerültek verziókezelésbe.

**A vizsgált fél kötelezettségei:** sudo jogú hozzáférés biztosítása, a konfigurációs fájlok átadása, valamint a konfiguráció változatlanul hagyása a két mérési pont között. A javítás csak a köztes jelentés után kezdődhetett.

## 2.5 Módszertan

| Módszer | Alkalmazás | Bizonyíték |
|---|---|---|
| Dokumentumvizsgálat | Dockerfile, compose.yaml, daemon.json, systemd unitok, auditd szabályok | a fájlok mérésenkénti másolata |
| Megfigyelés | `docker inspect`, `docker ps`, hálózatok, mount-pontok | parancskimenetek |
| Automatizált tesztelés | docker-bench-security (CIS 1-7.), Trivy image és config | nyers eszközkimenetek (log, JSON) |
| Manuális ellenőrzés | Minden WARN és PASS eredmény szúrópróbás ellenőrzése, eszköz-forráskód vizsgálata | elemzés (5.1-5.2 fejezet) |
| Újrateljesítés | Ugyanazon mérés megismétlése a javítások után, funkcionális teszt | v2 mérés, funkcionális teszt |

**Kockázatértékelés:** a kockázat a hatás és a bekövetkezési valószínűség függvénye, háromszintű skálán. A hatás a bizalmasság, a sértetlenség és a rendelkezésre állás sérülését jelenti, a valószínűség a kihasználhatóságot (hálózati elérhetőség, előfeltételek). A kezelési módok: javítás, felvállalás vagy áthárítás.

| Hatás \ Valószínűség | Alacsony | Közepes | Magas |
|---|---|---|---|
| **Magas** | Közepes | Magas | Kritikus |
| **Közepes** | Alacsony | Közepes | Magas |
| **Alacsony** | Alacsony | Alacsony | Közepes |

## 2.6 Időbeosztás

| Fázis | Tevékenység | Eredmény |
|---|---|---|
| Tervezés | Audit terv, tárgy és kizárások rögzítése | audit terv |
| Előkészítés | Host és v1 környezet telepítése | futó v1 környezet |
| Lebonyolítás I. | Első mérés, dokumentumvizsgálat | v1 mérés (2026-11-08 14:02 UTC) |
| Értékelés | Megállapítások, kockázatértékelés, akcióterv | 6. fejezet |
| Javítás | v2 környezet telepítése az akcióterv alapján | futó v2 környezet |
| Utókövetés | Újramérés, funkcionális teszt, összehasonlítás | v2 mérés (2026-11-08 15:14 UTC) |
| Jelentés | Jelen dokumentum, prezentáció | - |

# 3. A vizsgált rendszer

Az alkalmazás egy minimális CRUD webalkalmazás: időpontok listázása, foglalás (név, e-mail, időpont) és egy basic auth-tal védett admin nézet. Személyes adatot (nevet és e-mail-címet) kezel. Az alkalmazás kódja mindkét változatban azonos, csak a futtatókörnyezet változott.

**Architektúra (v1):** a három konténer egyetlen alapértelmezett compose-hálózaton osztozott, és mindhárom konténer publikált portot kapott a host összes interfészén: proxy 80, app 8000, db 5432. A jelszavak a `compose.yaml` `environment:` részében szerepeltek.

**Architektúra (v2):** a proxy az egyetlen publikált port (127.0.0.1:8080). Az app a `frontend` és a `backend` hálózaton is jelen van. Az adatbázis csak a belső (`internal: true`) `backend` hálózaton érhető el. A titkok Docker secretként, fájlból érkeznek.

| Jellemző | v1 (alapbeállítások) | v2 (akcióterv után) |
|---|---|---|
| Alap image | `python:latest`, `nginx:latest`, `postgres:latest` | rögzített verzió + digest, alpine |
| Futtató felhasználó | root (mindhárom) | app: 10001, db: postgres (70), proxy: nginx (101) |
| Titkok | env változó, compose fájlban | Docker secret (`/run/secrets`) |
| Publikált portok | 80, 8000, 5432 (`0.0.0.0`, `[::]`) | csak 8080 (`127.0.0.1`) |
| Hálózat | egy közös | `frontend` + belső `backend` |
| Erőforrás-korlát | nincs | memória, CPU shares, PID-limit |
| Root fájlrendszer | írható | `read_only` + tmpfs |
| Jogosultságok | alapértelmezett capability-k | `cap_drop: ALL`, `no-new-privileges` |
| AppArmor profil | `docker-default` | `docker-default` |
| Healthcheck | nincs | mindhárom image-ben |
| Restart policy | `always` | `on-failure:5` |
| Daemon (daemon.json) | nincs, alapértelmezett | icc, userns-remap, live-restore, userland-proxy, journald |
| Host auditálás | auditd fut, Docker-szabály nincs | auditd szabályok a Docker fájljaira |

## 3.1 A v1 kialakításának forrásai

A v1 környezetet szándékosan nem rontottuk el: a Docker alapértelmezéseit hagytuk érvényben, az adatbázis-szolgáltatást pedig a hivatalos postgres image dokumentációjának példája szerint állítottuk be [8]. Ez a példa tag nélküli (vagyis `latest`) image-et, `restart: always` policyt és környezeti változóban megadott jelszót használ, ugyanúgy, mint a v1. Az alábbi táblázat megmutatja, hogy a v1 egyes hiányosságai melyik alapértelmezésből vagy példából erednek, és mit mondanak róluk a nyilvános felmérések.

| Hiányosság (v1) | Honnan ered | Elterjedtség |
|---|---|---|
| Nem rögzített `latest` image | Tag nélkül a Docker a `latest` taget használja [5]. A tagek módosíthatók, ugyanazt az image-et csak a digest szerinti rögzítés garantálja [4]. | Shu et al. vizsgálatában a hivatalos és a közösségi image-ek több mint 80%-ában volt legalább egy magas súlyosságú sérülékenység [10]. A Sysdig 2022-es jelentése szerint az image-ek 75%-a tartalmaz javítható magas vagy kritikus sérülékenységet [9]. |
| Root futtatás (nincs `USER`) | A Docker ajánlása szerint a jogosultság nélkül is futtatható szolgáltatásnál a `USER` utasítással nem root felhasználóra kell váltani [4]. `USER` nélkül a v1 konténerei rootként futottak (4.3 fejezet). | A Sysdig 2022-es jelentése szerint a konténerek 76%-a rootként fut [9]. |
| Jelszó környezeti változóban | A hivatalos postgres példa a jelszót a `POSTGRES_PASSWORD` változóban adja meg [8]. A Docker dokumentációja szerint az így átadott jelszó véletlenül kiszivároghat, mert minden folyamat eléri, és naplókba is kerülhet [6]. | Dahlmanns et al. a Docker Hubról és privát registry-kből vizsgált image-ek 8,5%-ában talált titkot (Docker Hub: 9,0%) [11]. |
| Port publikálása minden interfészen | Host IP nélkül a Docker minden címen (`0.0.0.0`, `[::]`) publikálja a portot, amit a dokumentáció alapból nem biztonságosnak nevez [1]. A publikált port forgalma a ufw szabályait is megkerüli [2]. | A db port publikálása a v1-ben a környezet specifikációja szerint kényelmi okból történt. A hivatalos postgres példa nem publikálja. Elterjedtségére nincs hivatkozott felmérés. |
| Nincs erőforrás-korlát | Alapértelmezés szerint a konténernek nincs erőforrás-korlátja [3]. | Nincs hivatkozott felmérés. |
| `restart: always` | Az alapértelmezett policy a `no` [7]. Az `always` a hivatalos postgres példából származik [8]. | Nincs hivatkozott felmérés. |
| Nincs `daemon.json` | A fájl hiányában minden daemon-beállítás alapértelmezett, ezt a v1 mérés is mutatja (4.3 fejezet). | Nincs hivatkozott felmérés. |

# 4. Mérési bizonyítékok

## 4.1 Bizonyítékkezelés

A bizonyítékokat egy saját gyűjtőszkript rögzítette, mérésenként külön, időbélyeggel ellátott könyvtárba. Meglévő mérést a szkript nem ír felül. Egy mérés tartalmazza a host és az eszközök verzióit, a konfigurációs fájlok másolatát, a `docker inspect` és `docker ps` kimeneteit, a docker-bench és a Trivy nyers kimenetét, valamint egy mérési naplót a futtatott parancsokkal és hibákkal. Minden fájlról SHA-256 hash készült, így az utólagos módosítás kimutatható (`sha256sum -c`). A `docker inspect` kimenetben a jelszó-jellegű környezeti változók értékét a szkript a hash készítése előtt maszkolta. A nyers kimeneteket nem módosítottuk, az összesítés és az elemzés külön készült.

| Mérés | Időpont (UTC) | Szerep |
|---|---|---|
| v1 | 2026-11-08 14:02 | kiinduló állapot, elsődleges bizonyíték |
| v2 | 2026-11-08 15:14 | utókövetés az akcióterv végrehajtása után, elsődleges bizonyíték |
| v2 funkcionális teszt | 2026-11-08 15:16 | kiegészítő bizonyíték (4.4 fejezet) |
| v2, docker-bench `dash` alatt | 2026-11-08 14:24 | a T-1 eszközhiba igazolása (5.2 fejezet), értékelésre nem használtuk |

## 4.2 CIS Docker Benchmark: eredmények fejezetenként

A docker-bench 117 ellenőrzést futtatott. Az *INFO* és *NOTE* eredmények manuális értékelést igényelnek, és nem számítanak bele a pontszámba.

| CIS fejezet | PASS v1 | WARN v1 | PASS v2 | WARN v2 |
|---|---|---|---|---|
| 1 Host konfiguráció | 1 | 9 | 11 | 1 |
| 2 Docker daemon konfiguráció | 6 | 7 | 12 | 1 |
| 3 Daemon konfigurációs fájlok | 8 | 0 | 12 | 0 |
| 4 Image-ek és build fájlok | 1 | 3 | 4 | 1 |
| 5 Konténer runtime | 18 | 10 | 27 | 1 |
| 6 Security operations | 0 | 0 | 0 | 0 |
| **Összesen (1-6.)** | **34** | **29** | **66** | **4** |
| docker-bench score | **5** | | **61** | |

A 7. fejezet (Swarm) 9 ellenőrzése N/A, ezért kihagytuk. Az INFO eredmények egy része olyan fájlokra vonatkozik, amelyek ezen a disztribúción nem léteznek (pl. `/etc/default/docker`, `/etc/sysconfig/docker`). A 3. fejezet PASS-ainak növekedése (8 → 12) abból ered, hogy a v2-ben létrejött az `/etc/docker` könyvtár és a `daemon.json`, így azok jogosultságai is ellenőrizhetővé váltak.

## 4.3 A v1 mérés főbb bizonyítékai

**Root futtatás (CIS 4.1):** a docker-bench szerint `running as root: booking-proxy-1 booking-app-1 booking-db-1`. A `docker inspect` kimenetben mindhárom konténernél `Config.User = ""`. A Trivy config szkennelése is jelzi: *DS-0002 (HIGH): Specify at least 1 USER command in Dockerfile*.

**Nyílt titkok (CIS 4.10):** a compose fájl mérés közben rögzített másolatában a jelszavak nyílt szövegként szerepelnek (`POSTGRES_PASSWORD`, `DATABASE_URL`, `ADMIN_PASSWORD`). A `docker inspect` kimenetben ugyanezek a változók megjelennek (a bizonyítékban maszkolva: `***MASKED***`). Így bárki, akinek Docker API hozzáférése van, kiolvashatja őket.

**Publikált portok (CIS 5.9, 5.14):** a docker-bench kimenete `Containers with open ports: booking-proxy-1:80 booking-app-1:8000 booking-db-1:5432` és `port bound to wildcard IP: ...:0.0.0.0`, a `docker ps` kimenete pedig `0.0.0.0:5432->5432/tcp` bejegyzést mutat.

**Runtime korlátozások hiánya (CIS 5.11-5.13, 5.26, 5.29):** mindhárom konténer memória-, CPU- és PID-korlát nélkül, írható root fájlrendszerrel és `no-new-privileges` nélkül futott.

**Daemon (CIS 2.x):** nem létezett `/etc/docker/daemon.json`. WARN eredmény: icc (2.2), userns (2.9), authorization (2.12), naplózás (2.13), no-new-privileges (2.14), live-restore (2.15), userland-proxy (2.16).

**Host auditálás (CIS 1.1.3-1.1.18):** az auditd fut, de az `auditctl -l` kimenete *No rules*: a Docker binárisaira és fájljaira nincs auditszabály. Nyolc ilyen ellenőrzés WARN, a többi INFO (a fájl ezen a disztribúción nem létezik).

**Külön partíció (CIS 1.1.1):** a `findmnt` szerint a `/var/lib/docker` a gyökér-fájlrendszeren van (btrfs alkötet egy LUKS-titkosított eszközön), külön partíció nincs.

**AppArmor (CIS 5.2):** a hoston az AppArmor aktív, ezért a Docker mindhárom konténerre automatikusan a `docker-default` profilt alkalmazta (`AppArmorProfile: docker-default`). Az 5.2 ajánlás így már a v1-ben teljesült.

**Image sérülékenységek (CIS 4.4, Trivy):**

| Image (v1) | Alap OS | CRITICAL | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|
| booking-app:v1 (python:latest) | Debian 13.7 | 15 | 278 | 717 | 1304 |
| nginx:latest | Debian 13.7 | 1 | 67 | 125 | 168 |
| postgres:latest | Debian 13.7 | 2 | 91 | 162 | 144 |
| **Összesen** | | **18** | **436** | **1004** | **1616** |

A 454 magas vagy kritikus sérülékenységből mindössze 39-hez volt javított csomagverzió. A többség a teljes Debian alap image (fordítók, fejlesztői könyvtárak) felesleges csomagjaiból ered (CIS 4.3). Három forrás azonban nem a Debian alapból származik, ezért az alap image cseréjével nem szűnik meg: a postgres image-be épített `gosu` bináris elavult Go standard könyvtára (26 magas vagy kritikus), a python image-ben lévő pip beépített (vendorolt) csomagjai (urllib3, msgpack, setuptools; 5), valamint a libexpat, curl és zlib csomagok, amelyekhez az image cseréje mellett csomagfrissítés is kell.

**A `latest` tag rendelkezésre állási kockázata (megfigyelés):** a nem rögzített alap image kódváltozás nélkül is eltörheti az újraépítést. A projekt előkészítésekor (2026-11-07) a v1 első buildje így bukott el: a `python:latest` időközben a Python 3.15-re váltott, amelyhez a rögzített `psycopg-binary==3.2.10` csomagnak nem volt bináris változata. A build csak a függőség frissítése után sikerült.

## 4.4 A v2 mérés főbb bizonyítékai

A v2 image-ek rögzített, Alpine alapú image-ekre épülnek. Az image-cserével meg nem szűnő három sérülékenységforrást (4.3 fejezet) a Dockerfile-ok közvetlenül kezelik (M-04):

- **db:** a `gosu` törlése. Az entrypoint csak root futtatáskor hívja, ez a konténer pedig eleve `postgres` felhasználóval indul.
- **app:** a pip eltávolítása a függőségek telepítése után. A pip csak a buildhez kell.
- **proxy:** `apk upgrade` a build során, az Alpine biztonsági javításaival. A build idejére a felhasználó rootra vált, a konténer továbbra is a 101-es felhasználóval fut. Ennek ára, hogy az image tartalma a build időpontjától is függ. A ténylegesen mért image digestje a mérési bizonyítékban rögzített, a rendszeres újraépítést pedig az A-1 akciótervi pont kezeli.

| Image (v2) | Alap OS | CRITICAL | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|
| booking-app:v2 | Alpine 3.24.4 | 0 | 0 | 1 | 1 |
| booking-db:v2 | Alpine 3.24.4 | 0 | 0 | 1 | 0 |
| booking-proxy:v2 | Alpine 3.24.2 | 0 | 0 | 0 | 0 |

A Trivy config szkennelése a v2 Dockerfile-okban 0 hibát talált (v1: 3). Az `auditctl -l` a v2-ben 12 Docker-szabályt mutat. A 13. szabály (`/etc/containerd/config.toml`) nem töltődött be, mert a fájl ezen a hoston nem létezik, az 1.1.12 ellenőrzés ezért INFO. A daemon a `userns-remap` miatt külön tárolót használ (`/var/lib/docker/100000.100000`).

A funkcionális teszt (2026-11-08 15:16 UTC) szerint a v2 stack működik: a főoldal HTTP 200, a foglalás 302, az admin nézet hitelesítés nélkül és a régi jelszóval 401, a generált secrettel 200. A host hálózati címén a 80, 8000, 5432 és 8080 port zárt. Az app konténerben `uid=10001(app)`, ami a hoston a 110001-es UID-nak felel meg (userns-remap). A root fájlrendszer írása `Read-only file system` hibát ad, a környezeti változók között jelszó nincs, csak a `*_FILE` hivatkozások.

**Megfigyelés (telepítési szkript):** a v2 újratelepítésekor az app nem indult el, mert az adatbázis elutasította a jelszavát. Az ok: a telepítő szkript újratelepítéskor törölte a célkönyvtárat a titkokkal együtt, és új jelszót generált, a meglévő adatbázis-volume viszont az első inicializáláskor beállított jelszót őrizte. A szkript azóta a titkokat külön, újratelepítéskor megmaradó könyvtárban tárolja, az adatbázis-felhasználó jelszavát pedig a meglévő titokhoz igazítottuk. Az első telepítés üres volume-ra történt, ezért a hiba ott nem jelentkezett.

# 5. Elemzés

## 5.1 A docker-bench eredmények auditori ellenőrzése

Minden WARN eredményt összevetettünk a `docker inspect`, a konfigurációs fájlok és a mount-adatok bizonyítékaival. A PASS eredményeket szúrópróbaszerűen ellenőriztük, a gyanús eseteknél az eszköz forráskódja alapján. A manuális (*Manual*, *NOTE*) ajánlásokat külön értékeltük:

| CIS | Ajánlás | v1 értékelés | v2 értékelés |
|---|---|---|---|
| 4.2 | Megbízható alap image | Hivatalos image-ek, de nem rögzített tag | Hivatalos image-ek, digesttel rögzítve |
| 4.3 | Felesleges csomagok | Teljes Debian image, fordítókkal | Alpine, minimális |
| 4.4 | Szkennelés és újraépítés | Nincs folyamat, 454 H+C | Szkennelve és újraépítve, 0 H+C (M-04) |
| 4.8 | setuid/setgid bitek | Nincs eltávolítva | Az app image-ben eltávolítva |
| 4.10 | Titkok a Dockerfile-ban | Nincs a Dockerfile-ban, de a compose-ban igen | Nincs (secret) |
| 5.4 | Capability-k | Alapértelmezett készlet (az eszköz PASS-t ad, mert csak a hozzáadást vizsgálja) | `cap_drop: ALL` |
| 5.9 | Csak a szükséges portok | 3 port, ebből 2 felesleges | 1 port (szükséges, elfogadható) |
| 6.1-6.2 | Image és konténer sprawl | Nem értékelhető (1 projekt) | Nem értékelhető |

## 5.2 Az automatizált eszköz téves eredményei

| # | Ellenőrzés | Eszköz eredménye | Tényleges állapot | Ok (forráskód alapján) |
|---|---|---|---|---|
| T-1 | 2.2, 2.9 (érintett kód: 2.4, 2.5, 2.8, 2.12 is) | WARN (v2, `dash` alatt) | 2.2 és 2.9 megfelel | A szkript bash-szintaxist (`[[ ]]`) használ, de a dokumentáció `sh`-val futtatja. Ahol az `sh` a dash (pl. Ubuntu, Debian), ezek az ágak sosem teljesülnek. **Hamis pozitív.** |
| T-2 | 5.15 Restart policy | PASS (v1) | `restart: always`, nem felel meg | Az ellenőrzés csak `MaximumRetryCount > 5` esetén jelez. Az `always` policy értéke 0, ezért átmegy. **Hamis negatív.** |
| T-3 | 5.3 SELinux | WARN (v1), PASS (v2) | A hoston SELinux nincs, az LSM az AppArmor, így az ajánlás egyik változatra sem alkalmazható | Az ellenőrzés csak azt nézi, hogy a `SecurityOpt` nem üres. A v1-ben üres (**hamis pozitív**), a v2-ben a `no-new-privileges` kitölti (**formális megfelelés**). |

A T-1 miatt a docker-bench-et `bash`-sel futtattuk, az elsődleges v1 és v2 mérés így készült. A hibát egy külön, `dash` alatt futtatott v2 méréssel igazoltuk.

## 5.3 Következtetés az eszközről

Az eszköz kimenete gyors és jól megismételhető, de önmagában nem bizonyítja a megfelelést: 117 ellenőrzésből 4 esetben (2.2, 2.9, 5.15, 5.3) az eredmény nem tükrözte a valós állapotot, és az 5.4 PASS eredménye is csak a capability-k hozzáadását vizsgálja, az alapértelmezett készletet nem. Az auditban ezért minden megállapítást legalább egy független bizonyítékkal (inspect, konfigurációs fájl, mount-adat) is alátámasztottunk.

# 6. Megállapítások és kockázatértékelés

## 6.1 Megállapítások összesítése

| ID | Megállapítás | CIS | Hatás | Valósz. | Kockázat | NIST CSF |
|---|---|---|---|---|---|---|
| M-05 | Az adatbázis és az app portja minden interfészen publikálva, gyenge jelszóval | 5.9, 5.14, 5.8 | Magas | Magas | **Kritikus** | PR.AC-5 |
| M-02 | A konténerek root felhasználóval futnak | 4.1 | Magas | Közepes | **Magas** | PR.AC-4 |
| M-03 | A jelszavak nyílt szövegként szerepelnek a compose fájlban és a konténer környezetében | 4.10 | Magas | Közepes | **Magas** | PR.DS-1, PR.AC-1 |
| M-04 | Nem rögzített `latest` image-ek, 454 magas/kritikus sérülékenység | 4.2-4.4 | Közepes | Magas | **Magas** | ID.RA-1, PR.IP-12 |
| M-10 | A daemon alapbeállításokkal fut (icc, userns, live-restore, userland-proxy, naplózás) | 2.2, 2.9, 2.13-2.16 | Magas | Közepes | **Magas** | PR.PT-3 |
| M-01 | Nincs auditszabály a Docker daemonra és fájljaira | 1.1.3-1.1.18 | Közepes | Közepes | Közepes | DE.CM-3, PR.PT-1 |
| M-06 | Nincs memória-, CPU- és PID-korlát | 5.11, 5.12, 5.29 | Közepes | Közepes | Közepes | PR.DS-4 |
| M-07 | Írható root fájlrendszer | 5.13 | Közepes | Közepes | Közepes | PR.DS-6 |
| M-08 | Nincs `no-new-privileges`, alapértelmezett capability-k | 2.14, 5.26, 5.4 | Közepes | Közepes | Közepes | PR.AC-4 |
| M-09 | Nincs HEALTHCHECK | 4.6, 5.27 | Alacsony | Közepes | Alacsony | DE.CM-1 |
| M-11 | `restart: always` policy | 5.15 | Alacsony | Közepes | Alacsony | PR.PT-5 |
| M-12 | Nincs külön partíció a Docker adatainak | 1.1.1 | Közepes | Alacsony | Alacsony | PR.DS-4 |
| M-13 | Nincs authorization plugin és content trust | 2.12, 4.5 | Alacsony | Alacsony | Alacsony | PR.AC-4, PR.DS-6 |

**Megoszlás:** 1 kritikus, 4 magas, 4 közepes, 4 alacsony. Az M-10 a userns-remap hiánya miatt magas: userns nélkül a konténerben futó root UID megegyezik a host root UID-jével, így egy konténerkitörés host szintű kompromittálódást jelent. A CIS 5.2 (AppArmor) nem került a megállapítások közé, mert a v1-ben is teljesült (4.3 fejezet).

## 6.2 A legfontosabb megállapítások részletesen

### M-05: Felesleges, minden interfészen publikált portok (Kritikus)

**Tény:** a v1-ben a `db` konténer 5432-es és az `app` konténer 8000-es portja a host minden interfészén (`0.0.0.0`, `[::]`) elérhető volt. Az adatbázis jelszava (`booking123`) a compose fájlban nyílt szövegként szerepelt. **Elvárás (CIS 5.9, 5.14):** csak a szükséges portok legyenek nyitva, adott interfészhez kötve. **Kockázat:** a hálózatról közvetlenül elérhető adatbázis gyenge jelszóval a személyes adatok (név, e-mail) teljes kiszivárgását vagy módosítását teszi lehetővé. Az app közvetlen elérése megkerüli a proxy védelmeit. **Javaslat:** csak a proxy publikáljon portot, meghatározott interfészen. Az adatbázis kerüljön belső hálózatra. Kontroll: preventív. Kezelés: javítás.

### M-02: Root futtatás (Magas)

**Tény:** mindhárom konténer UID 0-val futott, a Dockerfile-ban nem volt `USER` utasítás. **Kockázat:** egy alkalmazásszintű kódfuttatási sérülékenység esetén a támadó a konténerben root jogot kap, ami a konténerkitörés esélyét és hatását növeli. **Javaslat:** dedikált, nem root felhasználó az image-ben (`USER`). Kontroll: preventív. Kezelés: javítás.

### M-03: Nyílt titkok (Magas)

**Tény:** a `POSTGRES_PASSWORD`, `DATABASE_URL` és `ADMIN_PASSWORD` értéke a verziókezelt `compose.yaml`-ban és a konténer környezeti változóiban szerepelt, és a `docker inspect` paranccsal kiolvasható volt. **Kockázat:** a titok a verziókezelőbe, a naplókba és a Docker API-hoz hozzáférő bármely felhasználóhoz eljut. **Javaslat:** Docker secret (fájl alapú, `/run/secrets`), az alkalmazás és a PostgreSQL a `*_FILE` változókon keresztül olvassa. A titkok generálása telepítéskor történjen, és ne kerüljenek a repóba. Kontroll: preventív. Kezelés: javítás.

### M-04: Nem rögzített, sérülékeny image-ek (Magas)

**Tény:** `latest` tagek, 18 kritikus és 436 magas súlyosságú sérülékenység. A `latest` váltása a projekt előkészítésekor egy build megszakadását is okozta (4.3 fejezet). **Kockázat:** ismert sérülékenységek kihasználása, nem reprodukálható build, váratlan üzemzavar. **Javaslat:** rögzített verzió és digest, minimális (alpine) alap image. Az image-cserével meg nem szűnő források kezelése: a `gosu` törlése, a pip eltávolítása a futtatási image-ből, csomagfrissítés a buildben. Rendszeres szkennelés és újraépítés. Kontroll: preventív. Kezelés: javítás.

### M-01: Hiányzó host-auditálás (Közepes)

**Tény:** az auditd fut, de nincs szabály a Docker binárisaira és konfigurációs fájljaira (`auditctl -l`: *No rules*). **Kockázat:** a Docker konfigurációjának vagy binárisainak jogosulatlan módosítása utólag nem deríthető fel. **Javaslat:** auditd szabályok a CIS 1.1.3-1.1.18 szerinti útvonalakra (`/etc/audit/rules.d/docker.rules`), a naplók központi gyűjtése. Kontroll: felismerő. Kezelés: javítás.

# 7. Akcióterv és utókövetés

## 7.1 Akcióterv és végrehajtás

| ID | Intézkedés | Kontroll | Kezelés | v1 | v2 | Állapot |
|---|---|---|---|---|---|---|
| M-05 | Csak a proxy publikál portot, `127.0.0.1:8080`, nem privilegizált port, db a belső hálózaton | preventív | javítás | WARN | PASS | Javítva |
| M-02 | `USER` minden image-ben (10001, postgres, 101) | preventív | javítás | WARN | PASS | Javítva |
| M-03 | Docker secret, `*_FILE` változók, telepítéskor generált titkok | preventív | javítás | NOTE | megfelel | Javítva |
| M-04 | Digesttel rögzített alpine image-ek, gosu és pip eltávolítva, Alpine csomagfrissítés a buildben, Trivy szkennelés | preventív | javítás | 454 H+C | 0 H+C | Javítva |
| M-10 | `daemon.json`: icc, userns-remap, live-restore, userland-proxy, no-new-privileges, journald | preventív | javítás | 7 WARN | PASS | Javítva (2.13 részben) |
| M-01 | auditd szabályok a Docker binárisaira és fájljaira, 12 szabály betöltve | felismerő | javítás | WARN | PASS | Javítva |
| M-06 | `mem_limit`, `cpu_shares`, `pids_limit` | preventív | javítás | WARN | PASS | Javítva |
| M-07 | `read_only: true` + tmpfs | preventív | javítás | WARN | PASS | Javítva |
| M-08 | `cap_drop: ALL`, `no-new-privileges` | preventív | javítás | WARN | PASS | Javítva |
| M-09 | HEALTHCHECK mindhárom image-ben | felismerő | javítás | WARN | PASS | Javítva |
| M-11 | `restart: on-failure:5` | hatáscsökkentő | javítás | PASS* | PASS | Javítva |
| M-12 | Külön partíció `/var/lib/docker` számára | hatáscsökkentő | felvállalás | WARN | WARN | Felvállalva |
| M-13 | Authorization plugin, content trust | preventív | felvállalás | WARN | WARN | Felvállalva |

\* Az eszköz hamis negatív eredménye (5.2 fejezet, T-2).

**A felvállalás indoklása:** M-12: egyetlen felhasználós, oktatási célú host, a lemez megtelésének hatása korlátozott, a titkosított btrfs gyökér-fájlrendszer átparticionálása aránytalan beavatkozás lenne. M-13: a hostot egyetlen adminisztrátor kezeli, a `docker` csoport egyetlen tagja maga az adminisztrátor (1.1.2). A Docker Content Trust (Notary v1) helyett a digest szerinti rögzítés biztosítja az image-ek sértetlenségét (kompenzáló kontroll). A 2.13 a journald miatt formálisan PASS, de távoli naplógyűjtés nincs, ezért csak részben teljesül.

## 7.2 Utókövetés: a két mérés összehasonlítása

| Mutató | v1 | v2 | Változás |
|---|---|---|---|
| docker-bench score | 5 | 61 | +56 |
| WARN (CIS 1-6.) | 29 | 4 | −86% |
| PASS (CIS 1-6.) | 34 | 66 | +94% |
| Trivy CRITICAL + HIGH | 454 | 0 | −100% |
| Trivy összes sérülékenység | 3180 | 3 | −99,9% |
| Trivy Dockerfile misconfiguration | 3 | 0 | −100% |
| Publikált portok | 3 (0.0.0.0) | 1 (127.0.0.1) | −2 |
| Root konténerek | 3 | 0 | −3 |

A v2-ben maradt 4 WARN: 1.1.1 a külön partíció (M-12), 2.12 és 4.5 az authorization plugin és a content trust (M-13), 5.9 pedig az egyetlen, szükséges proxy port, ami elfogadható.

## 7.3 Új akciótervi javaslatok (maradványkockázat)

| # | Javaslat | Felelős | Prioritás |
|---|---|---|---|
| A-1 | Rendszeres (pl. heti) Trivy szkennelés és újraépítés CI-ban, a CIS 4.4 folyamatos teljesítéséhez. A digest szerinti rögzítés miatt e nélkül az image-ek sérülékenységei idővel újra felhalmozódnak. | fejlesztő | magas |
| A-2 | Távoli naplógyűjtés (journald → központi syslog) a 2.13 teljes teljesítéséhez | rendszergazda | alacsony |
| A-3 | A proxy alap image digestjének frissítése, amint az upstream javított image megjelenik, és ezzel a build-idejű `apk upgrade` kiváltása | rendszergazda | alacsony |

# 8. Korlátok és következtetés

**Korlátok:**

- A vizsgált host egy natív Linuxot (Manjaro) futtató, egyfelhasználós munkaállomás, nem dedikált szerver. Az AppArmort a host előkészítésekor kapcsoltuk be (Manjaron alapból nem aktív, Ubuntun igen), ezért a CIS 5.2 már a v1-ben teljesült.
- Az audit két időpontra vonatkozó pillanatkép, a kontrollok működésének hatékonyságát egy időszakon át nem vizsgálta.
- Oktatási projekt lévén az auditor és az auditált fél egy csapat tagja, így a függetlenség korlátozott.
- Az interjú jegyzőkönyv sablonja elkészült, de a rendszergazdai szerepet a csapat töltötte be, ezért az interjús kérdéseket dokumentumvizsgálattal és technikai megfigyeléssel váltottuk ki.
- Az automatizált ellenőrzések lefedettsége és pontossága korlátozott (5.2 fejezet), a manuális ajánlások értékelése pedig az auditor szakmai megítélésén alapul.
- Az alkalmazás forráskódjának biztonsága nem volt része a vizsgálatnak.
- A v1-ben az adatbázis portjának publikálása kényelmi döntés volt, nem alapértelmezés, és a hivatalos postgres példa sem így teszi (3.1 fejezet). Az egyetlen kritikus megállapítás (M-05) súlyossága ezért részben ebből a döntésből ered.

**Következtetés:** az alapbeállításokkal, a hivatalos image-dokumentáció példája szerint telepített Docker környezet a CIS Docker Benchmark ajánlásainak jelentős részét nem teljesíti. A root konténerek, a nyílt titkok és a nem rögzített image-ek már az alapbeállításokból következnek, a kritikus kockázatot (M-05) pedig a kényelmi okból publikált adatbázis-port adta hozzá. A javasolt intézkedések nagy része a compose fájl és a Dockerfile-ok néhány sorával, az alkalmazás módosítása nélkül megvalósítható, és az utókövetés igazolta, hogy eredményesek. A fennmaradó kockázatokat a 7.3 fejezet akcióterve kezeli.

# Hivatkozások

A webes források elérésének dátuma: 2026-11-08.

- [1] Docker Docs: Port publishing and mapping. `https://docs.docker.com/engine/network/port-publishing/`
- [2] Docker Docs: Packet filtering and firewalls (Docker and ufw). `https://docs.docker.com/engine/network/packet-filtering-firewalls/`
- [3] Docker Docs: Resource constraints. `https://docs.docker.com/engine/containers/resource_constraints/`
- [4] Docker Docs: Building best practices (USER; Pin base image versions). `https://docs.docker.com/build/building/best-practices/`
- [5] Docker Docs: Dockerfile reference (FROM). `https://docs.docker.com/reference/dockerfile/`
- [6] Docker Docs: Manage secrets securely in Docker Compose. `https://docs.docker.com/compose/how-tos/use-secrets/`
- [7] Docker Docs: Start containers automatically. `https://docs.docker.com/engine/containers/start-containers-automatically/`
- [8] Docker Hub: postgres, Docker Official Image (How to use this image; Docker Secrets). `https://hub.docker.com/_/postgres`
- [9] Sysdig: Sysdig Usage and Security Report Finds More than 75% of Running Containers Have High-Risk Vulnerabilities. Sajtóközlemény a Sysdig 2022 Cloud-Native Security and Usage Reportról, 2022. január 26. `https://sysdig.com/press-releases/sysdig-usage-and-security-report-finds-more-than-75-of-running-containers-have-high-risk-vulnerabilities`
- [10] R. Shu, X. Gu, W. Enck: A Study of Security Vulnerabilities on Docker Hub. CODASPY '17, ACM, 2017. DOI: 10.1145/3029806.3029832
- [11] M. Dahlmanns, C. Sander, R. Decker, K. Wehrle: Secrets Revealed in Container Images: An Internet-wide Study on Occurrence and Impact. ASIA CCS '23, ACM, 2023, 797-811. DOI: 10.1145/3579856.3590329

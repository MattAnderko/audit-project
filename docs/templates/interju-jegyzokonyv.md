# Interjú jegyzőkönyv

| | |
|---|---|
| **Időpont** | _TBD_ |
| **Helyszín / mód** | _TBD (személyes / online)_ |
| **Interjúztató (auditor)** | _TBD_ |
| **Interjúalany (szerep)** | _TBD_ – rendszergazda / fejlesztő |
| **Kapcsolódó audit** | CIS Docker Benchmark audit, audit terv v_TBD_ |

> Módszer: érdeklődés és megerősítés (04. előadás). Ami a válaszokból kiderül, azt lehetőség szerint technikai bizonyítékkal is meg kell erősíteni (az „Ellenőrizve” oszlop).

## Kérdések

| # | Téma (CIS) | Kérdés | Válasz | Ellenőrizve (bizonyíték) |
|---|---|---|---|---|
| 1 | Általános | Mi a rendszer célja, kik használják, milyen adatokat kezel? | | |
| 2 | 1.1 Host | Milyen célra használt a host? Fut rajta más szolgáltatás is a Dockeren kívül? | | |
| 3 | 1.1 Host | Kik férnek hozzá a hosthoz? Ki van a `docker` csoportban? | | `getent group docker` |
| 4 | 1.1 Host | Hogyan és milyen gyakran frissül a host operációs rendszere és a Docker Engine? | | `docker version` |
| 5 | 1.1 / 6 | Van naplózás vagy auditálás a Docker fájlokra és a daemonra? | | `auditctl -l` |
| 6 | 2 Daemon | Módosítottátok a daemon alapbeállításait? Miért? | | `daemon.json` |
| 7 | 4 Image | Honnan származnak az alap image-ek? Rögzített verziót vagy `latest` taget használtok? | | Dockerfile |
| 8 | 4.4 Image | Szkennelitek és újraépítitek rendszeresen az image-eket? | | Trivy |
| 9 | 4.10 Image | Hogyan kezelitek a jelszavakat és kulcsokat (env, fájl, secret)? Kerülhet titok az image-be? | | Dockerfile, inspect |
| 10 | 5 Runtime | Milyen userrel futnak a konténerek? Van erőforrás-korlát? | | inspect |
| 11 | 5 Runtime | Mely portok vannak publikálva, és miért? | | `docker ps` |
| 12 | 6 | Van mentés az adatbázisról? Próbáltátok már visszaállítani? | | |
| 13 | 6 | Ki dönt a változtatásokról, és hogyan dokumentáljátok őket? | | git log |
| 14 | – | Vannak ismert eltérések vagy tudatosan felvállalt kockázatok? | | |

## Megjegyzések

_Szabad szöveg._

## Jóváhagyás

Az interjúalany a jegyzőkönyv tartalmát áttekintette, és az abban foglaltakat a valóságnak megfelelőnek ismeri el.

| Interjúalany | Auditor |
|---|---|
| _név, dátum_ | _név, dátum_ |

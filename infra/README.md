# A vizsgált környezet – specifikáció a rendszergazdának / fejlesztőnek

## Architektúra

```
            internet / host hálózat
                     │  :80 / :443
              ┌──────▼──────┐
              │   proxy     │  Nginx reverse proxy
              └──────┬──────┘
          frontend   │   (docker network)
              ┌──────▼──────┐
              │    app      │  időpontfoglaló webapp
              └──────┬──────┘
          backend    │   (docker network)
              ┌──────▼──────┐
              │     db      │  PostgreSQL + named volume
              └─────────────┘
   Host: Ubuntu Server LTS VM, Docker Engine + Compose v2
```

## Host

- **Valódi Linux VM** (VirtualBox, Hyper-V vagy felhő), nem Docker Desktop és nem WSL. A CIS 1–3. fejezet (host, daemon, daemon-fájlok) ellenőrzései csak így adnak értelmes eredményt.
- Ubuntu Server LTS, Docker Engine a hivatalos Docker apt repóból (`docker-ce`), Compose v2 plugin.
- Az auditor kap egy saját, sudo jogú felhasználót.

## Az alkalmazás (minimális)

Egyszerű CRUD, a stack szabadon választható (pl. Flask, FastAPI, Express):

- időpontok listázása, foglalás létrehozása (név, e-mail, időpont), foglalás törlése,
- egy egyszerű admin nézet (akár basic auth),
- PostgreSQL-ben tárolt adatok.

Az alkalmazás biztonsága **nem** tárgya az auditnak, a futtatókörnyezete viszont igen.

## v1 – „naiv” kiinduló telepítés (`infra/v1/`)

A cél egy **tipikus, alapbeállításokkal összerakott** környezet, ahogy egy átlagos tutorial alapján készülne. Ne legyen mesterségesen elrontva. Ami „magától” így lesz, az maradjon így:

| Jellemző | Tipikus v1 állapot |
|---|---|
| Alap image | `python:latest` / `node:latest`, `postgres:latest`, `nginx:latest` |
| Felhasználó | nincs `USER` a Dockerfile-ban, a konténer rootként fut |
| Titkok | jelszavak a `compose.yaml` `environment:` részében vagy `.env`-ben |
| Erőforrások | nincs memória-, CPU- vagy PID-limit |
| Fájlrendszer | írható root fájlrendszer, nincs `read_only` |
| Jogosultságok | nincs `cap_drop`, nincs `no-new-privileges` |
| Portok | a `db` és az `app` portja is publikálva a hostra (kényelmi okból) |
| Healthcheck | nincs `HEALTHCHECK` |
| Daemon | nincs `/etc/docker/daemon.json`, minden alapértelmezett |
| Host auditálás | nincs auditd szabály a Docker fájlokra |
| Restart | `restart: always` |

Ha valami a v1-ben eleve jól van megcsinálva, az is rendben van, ezt is dokumentáljuk (PASS).

## v2 – javított telepítés (`infra/v2/`)

A v2 az **auditor akcióterve alapján** készül, nem előre. Az alábbi lista csak tájékoztató jellegű (a CIS sorszámokat a használt benchmark verzióból kell kitölteni):

- Rögzített verziójú (vagy digestes), minimális alap image-ek (`-slim` / `-alpine`), frissítés, Trivy szerinti HIGH/CRITICAL CVE-k csökkentése
- Nem root felhasználó (`USER`) – CIS 4.1
- `HEALTHCHECK` a Dockerfile-ban
- Titkok Docker / Compose secretként, nem env-ben és nem az image-ben – CIS 4.10
- `mem_limit`, `cpus`, `pids_limit`
- `read_only: true` + `tmpfs` a szükséges könyvtáraknak
- `cap_drop: [ALL]`, csak a szükséges `cap_add`; `security_opt: [no-new-privileges:true]`
- Csak a `proxy` publikál portot. A `db` csak a belső `backend` hálózaton érhető el (`internal: true`).
- `restart: on-failure:5`
- `/etc/docker/daemon.json`: `icc: false`, `live-restore: true`, `userland-proxy: false`, `no-new-privileges: true`, naplózási beállítások
- auditd szabályok a Docker binárisra, a `/var/lib/docker`, `/etc/docker`, `docker.service` és `docker.sock` útvonalakra
- (opcionális) TLS az Nginx-en, adatbázis-mentés szkripttel

## Változáskezelés

- Minden konfigurációs változás git commit, a commit üzenetben a megállapítás azonosítójával (pl. `M-03: app konténer nem root userrel fut`).
- A v1 mérés és a köztes jelentés előtt a `infra/v1` nem változhat.

# Megállapítás sablon

> Minden megállapításhoz egy ilyen blokk tartozik. A jelentésben a részletes blokkok a fontosabbaknál szerepelnek, a többi összesítő táblába kerül.

---

### M-<sorszám>: <rövid cím, pl. „A konténerek root felhasználóval futnak”>

| Mező | Érték |
|---|---|
| **CIS hivatkozás** | pl. 4.1 *Ensure that a user for the container has been created* (Level 1, Automated) |
| **Érintett elem** | pl. `app`, `db` konténer |
| **Eszköz eredménye** | WARN / FAIL (docker-bench), vagy *Manual* |
| **Auditori ellenőrzés** | megerősítve / fals pozitív / részben |
| **Bizonyíték** | `evidence/<futás>/docker-bench/docker-bench.log`, sor: …; `docker/inspect-containers.json` → `Config.User` = `""` |
| **NIST CSF** | pl. PR.AC-4 (hozzáférési jogosultságok, legkisebb jogosultság) |

**Leírás (tény):** Mit tapasztaltunk, objektíven, mérhetően.

**Elvárás:** Mit ír elő a CIS ajánlás.

**Kockázat:**

| Hatás | Valószínűség | Kockázati szint |
|---|---|---|
| Magas / Közepes / Alacsony | Magas / Közepes / Alacsony | Kritikus / Magas / Közepes / Alacsony |

Indoklás: milyen fenyegetés, milyen kár (bizalmasság / sértetlenség / rendelkezésre állás).

**Javaslat:** konkrét, végrehajtható intézkedés.

| Kontrolltípus | Kezelési mód | Felelős | Határidő |
|---|---|---|---|
| preventív / felismerő / hatáscsökkentő / helyreállító | javítás / felvállalás / áthárítás | rendszergazda | … |

**Utókövetés (v2 mérés):** javítva / részben javítva / nem javítva / felvállalva. Bizonyíték: `evidence/<v2 futás>/…`

---

## Összesítő tábla (a jelentésbe)

| ID | CIS | Megállapítás | Kockázat | Kontroll | v1 | v2 |
|---|---|---|---|---|---|---|
| M-01 | 4.1 | Konténer root userrel fut | Magas | preventív | FAIL | PASS |
| … | | | | | | |

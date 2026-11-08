# v2 – adatbázis: rögzített verzió, nem root futás, HEALTHCHECK
FROM postgres:18.6-alpine@sha256:123b17998ccaf47e53b502e8c6a1e79afd8f579c6f3eec83c563da026f957395

# M-04: a gosu (Go bináris, elavult Go stdlib) csak akkor kell, ha a konténer rootként indul.
# Ez a konténer eleve postgres felhasználóval fut, az entrypoint így sosem hívja.
RUN rm -f /usr/local/bin/gosu

USER postgres

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" || exit 1

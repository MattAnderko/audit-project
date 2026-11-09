# v2 – hardened app image
# M-04: rögzített, digesttel azonosított, minimális alap image (CIS 4.2, 4.4)
FROM python:3.14-alpine@sha256:a18b20ad69e74df6cf6d2e1b1a260d7a1ecf5380fd83b310f83ba88c461cf894

# M-02: dedikált, nem root felhasználó (CIS 4.1)
RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 # M-04: a pip csak a buildhez kell; a futtatási image-ből eltávolítjuk a beépített
 # (vendorolt) csomagjaival együtt (urllib3, msgpack, setuptools sérülékenységek)
 && python -m pip uninstall -y pip \
 # CIS 4.8: setuid/setgid bitek eltávolítása
 && (find / -xdev -perm /6000 -type f -exec chmod a-s {} + 2>/dev/null || true)
COPY app.py .

USER 10001:10001
EXPOSE 8000

# M-09: HEALTHCHECK (CIS 4.6, 5.27)
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/healthz >/dev/null || exit 1

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "--worker-tmp-dir", "/tmp", "app:app"]

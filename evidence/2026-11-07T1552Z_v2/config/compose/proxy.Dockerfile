# v2 – reverse proxy: nem root nginx (8080-as port), a konfiguráció az image-be építve
FROM nginxinc/nginx-unprivileged:alpine@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Az alap image is a nginx (101) felhasználóval fut; explicit USER a Dockerfile-ban (CIS 4.1, Trivy DS-0002)
USER 101

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/nginx-health >/dev/null || exit 1

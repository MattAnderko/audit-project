#!/usr/bin/env bash
# A vizsgált host előkészítése (Ubuntu 24.04): Docker Engine, Trivy, docker-bench-security, auditd.
# Ez a v1 ("naiv") host-állapot: Docker a hivatalos repóból, alapértelmezett beállításokkal.
# Futtatás: sudo ./scripts/setup-host.sh
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q ca-certificates curl gnupg git jq auditd

install -m 0755 -d /etc/apt/keyrings

# Docker Engine (hivatalos repó)
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

# Trivy (Aqua Security repó)
curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor --yes -o /etc/apt/keyrings/trivy.gpg
echo "deb [signed-by=/etc/apt/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" \
  > /etc/apt/sources.list.d/trivy.list

apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin trivy
systemctl enable --now docker

# docker-bench-security (CIS Docker Benchmark automatizált ellenőrzés)
if [[ ! -d /opt/docker-bench-security ]]; then
  git clone --depth 1 https://github.com/docker/docker-bench-security.git /opt/docker-bench-security
fi

# A felhasználó a docker csoportba (tipikus "tutorial" lépés – a v1 része)
if [[ -n "${SUDO_USER:-}" ]]; then usermod -aG docker "$SUDO_USER"; fi

docker version --format 'Docker {{.Server.Version}}'
trivy --version | head -1
git -C /opt/docker-bench-security rev-parse --short HEAD

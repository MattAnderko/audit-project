#!/usr/bin/env bash
# AppArmor bekapcsolása Manjaro / Arch hoston (CIS 5.2, M-12): az "apparmor" LSM hozzáadása a kernel boot paramétereihez.
# A /etc/default/grub fájlról időbélyeges mentés készül. Utána újraindítás szükséges.
# Futtatás: sudo ./scripts/enable-apparmor-grub.sh
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "sudo szükséges: sudo $0" >&2; exit 1; }

GRUB=/etc/default/grub
LSM="lsm=landlock,lockdown,yama,integrity,apparmor,bpf"

if grep -qw apparmor /sys/kernel/security/lsm 2>/dev/null; then
  echo "Az AppArmor már aktív: $(cat /sys/kernel/security/lsm)"; exit 0
fi
if grep -q '^GRUB_CMDLINE_LINUX_DEFAULT=.*lsm=' "$GRUB"; then
  echo "A $GRUB már tartalmaz lsm= paramétert, kézzel ellenőrizd:" >&2
  grep '^GRUB_CMDLINE_LINUX_DEFAULT=' "$GRUB" >&2
  exit 1
fi

BACKUP="$GRUB.bak-$(date +%Y%m%d%H%M%S)"
cp -p "$GRUB" "$BACKUP"
# egyszeres és dupla idézőjeles formát is kezel (a Manjaro egyszerest használ)
sed -i -E "s|^(GRUB_CMDLINE_LINUX_DEFAULT=)([\"'])(.*)\\2[[:space:]]*\$|\\1\\2\\3 ${LSM}\\2|" "$GRUB"
if ! grep -q "^GRUB_CMDLINE_LINUX_DEFAULT=.*${LSM}" "$GRUB"; then
  cp -p "$BACKUP" "$GRUB"
  echo "Nem sikerült módosítani a $GRUB fájlt, visszaállítva. Kézzel add hozzá: ${LSM}" >&2
  exit 1
fi
echo "Mentés: $BACKUP"
grep '^GRUB_CMDLINE_LINUX_DEFAULT=' "$GRUB"

if command -v update-grub >/dev/null 2>&1; then update-grub; else grub-mkconfig -o /boot/grub/grub.cfg; fi

echo
echo "Kész. Indítsd újra a gépet, utána ellenőrzés: cat /sys/kernel/security/lsm (az 'apparmor' szerepeljen benne)."
echo "Visszaállítás: sudo cp $BACKUP $GRUB && sudo update-grub"

#!/usr/bin/env bash
# Собирает пакет outertale-ru для Arch Linux из оригинального app.asar.
#
# Использование:
#   ./packaging/build-package.sh [путь-к-оригинальному-app.asar]
#
# По умолчанию берётся /usr/share/outertale/app.asar (пакет outertale из AUR).
# Требуются: asar, base-devel, установленный electron.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/packaging/work"
BASE_ASAR="${1:-/usr/share/outertale/app.asar}"

if [[ ! -f "$BASE_ASAR" ]]; then
   if [[ -f /usr/share/outertale-ru/app.asar ]]; then
      BASE_ASAR=/usr/share/outertale-ru/app.asar
      echo "Внимание: оригинальный app.asar не найден, использую уже пропатченный."
   else
      echo "Не найден app.asar. Установите outertale из AUR или укажите путь аргументом." >&2
      exit 1
   fi
fi

command -v asar >/dev/null || { echo "Не найден asar. Установите пакет asar." >&2; exit 1; }
command -v makepkg >/dev/null || { echo "Не найден makepkg. Установите base-devel." >&2; exit 1; }

if [[ ! -f "$ROOT/mods/ru_RU/index.js" ]]; then
   echo "Мод не собран. Сначала выполните: python3 tools/build_mod.py" >&2
   exit 1
fi

rm -rf "$WORK"
mkdir -p "$WORK"
echo "Распаковываю $BASE_ASAR..."
asar extract "$BASE_ASAR" "$WORK/app"

echo "Патчу игру..."
python3 "$ROOT/packaging/patch_game.py" "$WORK/app"

echo "Добавляю мод..."
rm -rf "$WORK/app/mods/ru_RU"
mkdir -p "$WORK/app/mods"
cp -R "$ROOT/mods/ru_RU" "$WORK/app/mods/ru_RU"

echo "Упаковываю app.asar..."
asar pack "$WORK/app" "$WORK/app.asar"

cp "$ROOT/packaging/PKGBUILD" "$WORK/PKGBUILD"
cp "$ROOT/packaging/outertale-ru.sh" "$WORK/outertale-ru.sh"
cp "$ROOT/packaging/outertale-ru.desktop" "$WORK/outertale-ru.desktop"
cp "$ROOT/packaging/icon.png" "$WORK/icon.png"

echo "Собираю пакет..."
cd "$WORK"
makepkg -f --noconfirm

echo
echo "Готовый пакет:"
ls -lh "$WORK"/outertale-ru-*.pkg.tar.zst

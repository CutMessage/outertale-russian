#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/mods/ru_RU"

if [[ ! -f "$SRC/index.js" ]]; then
   echo "Ошибка: не найден $SRC/index.js" >&2
   echo "Соберите мод командой: python3 tools/build_mod.py" >&2
   exit 1
fi

case "$(uname -s)" in
   Darwin)
      MODS_DIR="$HOME/Library/Preferences/spacetime/mods"
      ;;
   Linux)
      MODS_DIR="$HOME/.config/spacetime/mods"
      ;;
   *)
      echo "Эта система не поддерживается install.sh. Установите вручную:" >&2
      echo "  скопируйте mods/ru_RU в <папка spacetime>/mods/ru_RU" >&2
      exit 1
      ;;
esac

DEST="$MODS_DIR/ru_RU"
mkdir -p "$MODS_DIR"

if [[ -e "$DEST" ]]; then
   BACKUP="$DEST.backup.$(date +%Y%m%d-%H%M%S)"
   mv "$DEST" "$BACKUP"
   echo "Предыдущая версия мода сохранена: $BACKUP"
fi

cp -R "$SRC" "$DEST"
echo "Мод установлен: $DEST"
echo "Запустите Outertale. При первом запуске русский язык включится автоматически."
echo "Сменить язык можно в настройках: ЯЗЫК (LANGUAGE)."

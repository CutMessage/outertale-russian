#!/usr/bin/env bash
set -euo pipefail

case "$(uname -s)" in
   Darwin)
      DEST="$HOME/Library/Preferences/spacetime/mods/ru_RU"
      ;;
   Linux)
      DEST="$HOME/.config/spacetime/mods/ru_RU"
      ;;
   *)
      echo "Поддерживаются только Linux и macOS. На Windows удалите папку:"
      echo "  %APPDATA%\\spacetime\\mods\\ru_RU"
      exit 1
      ;;
esac

if [[ ! -d "$DEST" ]]; then
   echo "Мод не найден: $DEST"
   exit 0
fi

echo "Перед удалением переключите язык на English в настройках игры."
read -r -p "Удалить $DEST? [y/N] " answer
case "$answer" in
   [yY]|[yY][eE][sS])
      rm -rf "$DEST"
      echo "Удалено."
      ;;
   *)
      echo "Отменено."
      ;;
esac

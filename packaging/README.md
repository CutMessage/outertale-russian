# Сборка пакета для Arch Linux

Обычным пользователям достаточно `./install.sh` — мод ставится в
`~/.config/spacetime/mods` и не трогает файлы игры.

Этот способ нужен, если хочется отдельный пакет `outertale-ru`, который
заменяет `outertale` и содержит мод внутри `app.asar`.

## Что нужно

- Установленный `outertale` из AUR (нужен оригинальный `app.asar`).
- Пакеты `asar`, `base-devel`, `electron`.

## Сборка

```bash
python3 tools/build_mod.py
./packaging/build-package.sh
```

Скрипт:

1. распаковывает `/usr/share/outertale/app.asar`;
2. патчит `index.js` и `preload.js`;
3. встраивает `mods/ru_RU`;
4. собирает пакет через `makepkg`.

Готовый файл появится в `packaging/work/outertale-ru-*.pkg.tar.zst`.

## Установка

```bash
sudo pacman -U packaging/work/outertale-ru-*.pkg.tar.zst
```

Пакет `outertale-ru` конфликтует с `outertale`, поэтому pacman предложит
удалить оригинал. Сохранения лежат отдельно и не удаляются.

Если оригинальный `app.asar` уже потерян, скрипт возьмёт
`/usr/share/outertale-ru/app.asar` (предыдущую версию пакета) и пересоберёт
её с новым модом.

# Outertale — русская локализация

Неофициальный русский перевод для **Outertale** (Project Spacetime 5.04).

![Русское интро](docs/intro-1.png)

## Что это

- Мод для Outertale, добавляющий язык `ru_RU`.
- Основа — перевод сообщества с Weblate (проект `ps-outertale`): 4 041 строка.
- Ещё 22 699 строк переведены машинно (Google Translate) и постепенно правятся вручную.
- Всего в словаре 26 741 строка; 388 служебных строк (имена файлов, коды, форматы) оставлены на английском.
- Игровые теги, цвета, шрифты и переносы строк сохраняются.
- Служебные строки и имена файлов остаются на английском; английский используется как запасной язык.

> Большая часть текста переведена машинно: возможны неточные падежи, калька и неудачные формулировки. Исправления приветствуются.

## Установка

### Готовый архив

Самый простой способ — скачать [`outertale-ru-mod.zip`](https://github.com/CutMessage/outertale-russian/releases/latest) со страницы релизов и распаковать папку `ru_RU` в папку `spacetime/mods`:

- Linux: `~/.config/spacetime/mods/`
- macOS: `~/Library/Preferences/spacetime/mods/`
- Windows: `%APPDATA%\spacetime\mods\`

В архиве только мод (около 1 МБ), файлы игры не входят.

### Linux и macOS

1. Установите Outertale 5.04.
2. Склонируйте репозиторий и запустите установщик:

   ```bash
   git clone https://github.com/CutMessage/outertale-russian.git
   cd outertale-russian
   ./install.sh
   ```

3. Запустите игру. При первом запуске русский включится автоматически.

Мод копируется в:

- Linux: `~/.config/spacetime/mods/ru_RU`
- macOS: `~/Library/Preferences/spacetime/mods/ru_RU`

### Windows

Скопируйте папку `mods/ru_RU` в `%APPDATA%\spacetime\mods\ru_RU` или запустите PowerShell:

```powershell
.\install.ps1
```

### Вручную

Скопируйте `mods/ru_RU` в папку `spacetime/mods`. Язык можно выбрать в настройках: **ЯЗЫК → ru_RU**. При первом запуске мод включает его сам.

## Как это выглядит

| Интро | Второй экран |
| --- | --- |
| ![Интро](docs/intro-1.png) | ![Второй экран](docs/intro-2.png) |

## Удаление

1. Переключите язык на English в настройках игры.
2. Удалите папку `ru_RU` из `spacetime/mods`.

На Linux и macOS:

```bash
./uninstall.sh
```

Сохранения и настройки не затрагиваются.

## Совместимость

- Outertale 5.04 (Project Spacetime, внутренняя версия 5.0.3).
- Мод не меняет файлы игры и работает из пользовательской папки.
- Сохранения остаются в `~/.config/spacetime` (Linux).
- Для Arch Linux есть опциональная сборка пакета `outertale-ru` — см. [`packaging/README.md`](packaging/README.md).

## Разработка

Структура:

- `mods/ru_RU/index.js` — готовый мод (генерируется).
- `src/weblate-ru.json` — переводы Weblate.
- `src/machine-ru.json` — машинный перевод.
- `src/overrides.json` — ручные правки.
- `src/fonts.json` — пути к шрифтам.
- `tools/` — загрузка строк, перевод и сборка.

Пересобрать мод:

```bash
python3 tools/build_mod.py
```

Проверить, что `index.js` соответствует исходникам:

```bash
python3 tools/build_mod.py --check
```

Обновить машинный перевод (нужен Python 3 и интернет):

```bash
python3 tools/fetch_units.py
python3 tools/mt.py run
python3 tools/export_mt.py
python3 tools/build_mod.py
```

Ручные исправления удобнее добавлять в `src/overrides.json`: ключ — точная английская строка, значение — русский перевод.

## Авторы и права

- **Outertale** — spacey_432 и команда **Project Spacetime**. Официальный движок: <https://gitgud.io/spacey432/spacetime>.
- Оригинальный текст, спрайты, музыка, шрифты и другие ресурсы игры принадлежат spacey_432 и участникам Project Spacetime.
- **Русский перевод Weblate** — участники проекта `ps-outertale`.
- **Шрифты с кириллицей** — из русской локализации Outertale.
- **Машинный перевод** — Google Translate.
- **Мод-обёртка, установщики и инструменты** — CutMessage и участники этого репозитория.

Это неофициальный фанатский перевод. Репозиторий и релизы содержат только мод перевода и не включают файлы игры: для запуска нужна официальная Outertale 5.04. Если вы автор игры и хотите изменить условия распространения перевода — создайте issue.

## English

Fan-made Russian localization mod for Outertale 5.04. Copy `mods/ru_RU` into your `spacetime/mods` folder (or run `./install.sh` on Linux/macOS). Russian is enabled automatically on first launch; you can switch languages in Settings → LANGUAGE. Most strings are machine-translated; corrections are welcome. This repository contains no game files.

## Отказ от ответственности

Это фанатский проект, не связанный с авторами Outertale. Права на игру, оригинальные тексты, шрифты и другие ресурсы принадлежат их авторам. Репозиторий не содержит файлов игры.

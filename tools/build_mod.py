# Собирает мод mods/ru_RU/index.js из исходных словарей.
#
# Использование:
#   python3 tools/build_mod.py          # пересобрать мод
#   python3 tools/build_mod.py --check  # проверить, что мод совпадает с исходниками
#
# Источники:
#   src/weblate-ru.json  — переводы сообщества Weblate
#   src/machine-ru.json  — машинный перевод
#   src/overrides.json   — ручные правки (имеют наивысший приоритет)
#   src/fonts.json       — пути к шрифтам с кириллицей

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mt import TOKEN, should_skip  # noqa: E402

SRC = os.path.join(ROOT, 'src')
MOD_DIR = os.path.join(ROOT, 'mods', 'ru_RU')
MOD_FILE = os.path.join(MOD_DIR, 'index.js')

# Имена персонажей приводим к вариантам, уже принятым в русском переводе.
NAME_FIXES = [
    ('Асгор', 'Азгор'),
    ('Асриэл', 'Азриэл'),
    ('Ундайн', 'Андайн'),
    ('Ториель', 'Ториэль'),
    ('ТУСКУЙТЕСЬ', 'ТУСИТЕСЬ'),
    ('тускуйтесь', 'тусите'),
]

# Названия мест и персонажей, которые машинный перевод оставил латиницей.
# Пары (английское название, канонический русский вариант).
TERM_FIXES = [
    # Составные названия идут раньше коротких, чтобы замениться целиком.
    ('Flamin\' Grillby', 'Горящий Гриллби'),
    ('Grillby\'s', 'Гриллби'),
    ('Astro Serf', 'Шипонавт'),
    ('Canis Major', 'Большой Пёс'),
    ('Canis Minor', 'Малый Пёс'),
    ('Monster Kid', 'Монстрёнок'),
    ('Mew Mew Space Adventure', 'Космическое приключение Мяу-Мяу'),
    ('Mew Mew', 'Мяу-Мяу'),
    ('Moon Rocks', 'Лунные камни'),
    ('Free Bones', 'Бесплатные кости'),
    ('LOVE OIL', 'МАСЛО ЛЮБВИ'),
    ('LAZER DELUXE', 'ЛАЗЕР ДЕЛЮКС'),
    ('Grand Blook', 'Гранд Блук'),
    ('Hyper Vortex Pop', 'Гипер Вихрь Поп'),
    ('Fabulous Faraday', 'Великолепный Фарадей'),
    ('Bishie Cream', 'Биши'),
    ('TEM SHOP', 'МАГАЗИН ТЕМ'),
    ('Corn Dog', 'Кукурдог'),
    ('NEO ENERGY', 'НЕО-ЭНЕРГИЯ'),
    ('Chilldrake', 'Хладоцып'),
    ('Stardrake', 'Луноцып'),
    ('Whizkarat', 'Мышеус'),
    ('OuterNet', 'Аутернет'),
    ('Aerialis', 'Стратополис'),
    ('Starton', 'Звездоград'),
    ('Outlands', 'Запределье'),
    ('Foundry', 'Литейная'),
    ('Citadel', 'Цитадель'),
    ('Grillbz', 'Гриллбз'),
    ('Grillby', 'Гриллби'),
    ('MTT', 'МТТ'),
    ('CORE', 'Ядро'),
    # Имена персонажей.
    ('Undyne', 'Андайн'),
    ('Papyrus', 'Папирус'),
    ('Alphys', 'Альфис'),
    ('Mettaton', 'Меттатон'),
    ('Napstablook', 'Напстаблук'),
    ('Toriel', 'Ториэль'),
    ('Asgore', 'Азгор'),
    ('Asriel', 'Азриэль'),
    ('Frisk', 'Фриск'),
    ('Muffet', 'Маффет'),
    ('Temmie', 'Темми'),
    ('Sans', 'Санс'),
]

# Разбиваем строку на игровые теги и обычный текст.
TAG_SPLIT = re.compile(f'({TOKEN.pattern})')


def keep_case(match, replacement):
    """Сохраняет регистр исходного названия: КАПС, С Заглавной или строчный."""
    if match.isupper():
        return replacement.upper()
    if match.islower():
        return replacement.lower()
    return replacement


def fix_terms(text):
    """Заменяет названия только в тексте, не трогая содержимое игровых тегов."""
    parts = TAG_SPLIT.split(text)
    for i in range(0, len(parts), 2):
        chunk = parts[i]
        # Если весь текст реплики написан капсом, названия тоже пишем капсом.
        loud = chunk.isupper()
        for english, russian in TERM_FIXES:
            if english == 'CORE':
                # CORE — аббревиатура, но по-русски это обычное слово «Ядро».
                repl = (lambda m: 'ЯДРО') if loud else (lambda m: 'Ядро')
            else:
                # Строчные совпадения не трогаем: это обычные слова, а не имена.
                repl = lambda m: (
                    m.group(0) if m.group(0).islower()
                    else keep_case(m.group(0), russian)
                )
            chunk = re.sub(
                r'(?<![A-Za-z])' + re.escape(english) + r'(?![A-Za-z])',
                repl,
                chunk,
                flags=re.IGNORECASE,
            )
        parts[i] = chunk
    return ''.join(parts)


def postprocess(source, target):
    """Правит типичные ошибки машинного перевода."""
    for old, new in NAME_FIXES:
        target = target.replace(old, new)
    target = fix_terms(target)
    if 'DETERMINATION' in source.upper():
        target = (target
                  .replace('ОПРЕДЕЛЕНИЕ', 'РЕШИМОСТЬ')
                  .replace('Определение', 'Решимость')
                  .replace('определение', 'решимость')
                  .replace('ОПРЕДЕЛЁННОСТЬ', 'РЕШИМОСТЬ')
                  .replace('Определённость', 'Решимость')
                  .replace('определённость', 'решимость'))
    return target


def js(value, indent=None):
    """Сериализует данные в JavaScript-совместимый JSON."""
    text = json.dumps(
        value,
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
        separators=(',', ':') if indent is None else None,
    )
    return text.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def build():
    weblate = json.load(open(os.path.join(SRC, 'weblate-ru.json')))
    machine = json.load(open(os.path.join(SRC, 'machine-ru.json')))
    overrides = json.load(open(os.path.join(SRC, 'overrides.json')))
    fonts = json.load(open(os.path.join(SRC, 'fonts.json')))

    dictionary = {}
    for source, target in weblate.items():
        if isinstance(source, str) and isinstance(target, str) and target.strip():
            dictionary[source] = target

    added = 0
    skipped = 0
    duplicate = 0
    for source, target in machine.items():
        if should_skip(source):
            skipped += 1
            continue
        if not target.strip():
            continue
        # Человеческий перевод с Weblate всегда важнее машинного.
        if source in dictionary:
            duplicate += 1
            continue
        dictionary[source] = postprocess(source, target)
        added += 1

    # Ручные правки применяем последними.
    for source, target in overrides.items():
        dictionary[source] = target

    for source, target in dictionary.items():
        if '⟦' in target:
            raise SystemExit(f'В переводе остался маркер: {source!r} -> {target!r}')

    code = f"""// Сгенерировано tools/build_mod.py. Не редактировать вручную.
const DICT = {js(dictionary)};

const CONTENT = {js(fonts, 3)};

function translate (value) {{
   if (typeof value === 'string') return DICT[value] ?? value;
   if (typeof value === 'function') {{
      return function (...args) {{
         const result = value.apply(this, args);
         return result && typeof result.then === 'function' ? result.then(translate) : translate(result);
      }};
   }}
   if (Array.isArray(value)) return value.map(translate);
   if (value && typeof value === 'object') {{
      const result = {{}};
      for (const key of Object.keys(value)) result[key] = translate(value[key]);
      return result;
   }}
   return value;
}}

export default async function (name, api) {{
   const {{ translator, SAVE }} = api;
   if (translator.langs.includes('ru_RU')) return;
   translator.langs.push('ru_RU');
   translator.content.addLanguage('ru_RU', CONTENT);
   for (const [ key, entry ] of translator.registry) {{
      entry.addLanguage('ru_RU', translate(entry.defaults));
   }}
   translator.values.addLanguage('ru_RU', translate(translator.values.defaults));
   if (!SAVE.manager.getItem('OUTERTALE_RU_INITIALIZED')) {{
      SAVE.manager.setItem('OUTERTALE_RU_INITIALIZED', '1');
      SAVE.flag.s.$option_language = 'ru_RU';
   }}
   console.log('OUTERTALE-RU loaded:', Object.keys(DICT).length, 'strings');
}}
"""
    os.makedirs(MOD_DIR, exist_ok=True)
    return dictionary, added, skipped, duplicate, code


def main():
    dictionary, added, skipped, duplicate, code = build()
    check = '--check' in sys.argv
    if check:
        if not os.path.exists(MOD_FILE):
            raise SystemExit('mods/ru_RU/index.js отсутствует — запустите сборку')
        current = open(MOD_FILE).read()
        if current != code:
            raise SystemExit('mods/ru_RU/index.js не совпадает с исходниками — пересоберите мод')
        print('проверка пройдена, строк:', len(dictionary))
        return
    open(MOD_FILE, 'w').write(code)
    print('строк в словаре:', len(dictionary))
    print('из них машинных:', added, 'пропущено служебных:', skipped)
    if duplicate:
        print('машинных строк, перекрытых Weblate:', duplicate)
    print('записано:', MOD_FILE, f'({len(code)} байт)')


if __name__ == '__main__':
    main()

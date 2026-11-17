# Сохраняет накопленный машинный перевод из cache/mt-progress.json
# в src/machine-ru.json (без служебных строк, которые мы не переводим).
#
# Использование:
#   python3 tools/export_mt.py

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mt import should_skip  # noqa: E402

CACHE = os.path.join(ROOT, 'cache')
SRC = os.path.join(ROOT, 'src')


def main():
    progress_path = os.path.join(CACHE, 'mt-progress.json')
    if not os.path.exists(progress_path):
        raise SystemExit('Нет cache/mt-progress.json — сначала запустите tools/mt.py')
    progress = json.load(open(progress_path))
    done = progress.get('done', {})
    result = {}
    for source, target in done.items():
        if should_skip(source):
            continue
        if not target.strip():
            continue
        result[source] = target
    os.makedirs(SRC, exist_ok=True)
    path = os.path.join(SRC, 'machine-ru.json')
    json.dump(result, open(path, 'w'), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    print('сохранено строк:', len(result), 'в', path)


if __name__ == '__main__':
    main()

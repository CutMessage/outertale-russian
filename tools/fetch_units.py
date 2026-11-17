# Загружает строки русского перевода проекта ps-outertale из Weblate.
# Результат: cache/<компонент>-units.json
#
# Использование:
#   python3 tools/fetch_units.py

import json
import os
import time
import urllib.request

BASE = 'https://translate.ws3917.space:29271/api/translations/ps-outertale'
COMPONENTS = [
    '0-systems', '1-outlands', '2-starton', '3-foundry',
    '4-aerialis', '5-citadel', '6-common', '7-values',
]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'cache')


def main():
    os.makedirs(CACHE, exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0'}
    for comp in COMPONENTS:
        url = f'{BASE}/{comp}/ru/units/?page_size=1000'
        units = []
        while url:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.load(response)
            units.extend(data['results'])
            url = data.get('next')
            print(comp, 'загружено', len(units), 'из', data['count'], flush=True)
            time.sleep(0.1)
        path = os.path.join(CACHE, f'{comp}-units.json')
        json.dump(units, open(path, 'w'), ensure_ascii=False)
        translated = sum(
            1 for u in units
            if u.get('translated') and any(x.strip() for x in u.get('target', []))
        )
        print(comp, 'сохранено', len(units), 'переведено', translated, flush=True)


if __name__ == '__main__':
    main()

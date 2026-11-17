# Машинный перевод недостающих строк через Google Translate.
#
# Использование:
#   python3 tools/mt.py status              # сколько строк переведено и осталось
#   python3 tools/mt.py sample              # пробный перевод первых 120 строк
#   python3 tools/mt.py run                 # перевести всё недостающее (8 потоков)
#   python3 tools/mt.py run --workers 4     # указать число потоков
#
# Исходные строки лежат в cache/*-units.json (см. tools/fetch_units.py).
# Прогресс сохраняется в cache/mt-progress.json, его можно безопасно прерывать.
# Уже выгруженный перевод из src/machine-ru.json подхватывается автоматически.

import concurrent.futures
import glob
import json
import os
import random
import re
import sys
import threading
import time
import urllib.parse
import urllib.request

BASE = 'https://translate.googleapis.com/translate_a/t?client=gtx&sl=en&tl=ru'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'cache')
PROGRESS = os.path.join(CACHE, 'mt-progress.json')

# Игровые теги, которые нельзя отдавать переводчику.
TOKEN = re.compile(
    r'\$\([^)]*\)'
    r'|\{[^{}]*\}'
    r'|<[^<>]{1,40}>'
    r'|\[[A-Z0-9 /]{1,20}\]'
    r'|§[^§\n]{1,60}§'
    r'|\\x[0-9a-fA-F]{2}'
    r'|\\u[0-9a-fA-F]{4}'
)
MARK = re.compile(r'⟦XQ(\d+)QX⟧')

# Служебные строки, которые лучше оставить на английском.
FILENAME = re.compile(r'\.(?:kwac|png|jpe?g|gif|ogg|mp3|wav|json|js|ts|ttf|csv|txt|html|css|asar)\b', re.I)
CAMEL = re.compile(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+$')
IDENT = re.compile(r'^(?=.*[_\-.])[A-Za-z0-9_.\-/]+$')
FORMAT_ONLY = re.compile(r'^\$\([^)]*\)[a-zA-Z%]*(?:/[a-zA-Z]+)?$')
SKIP_EXACT = {'GODHOME', 'REGISTRY', 'EXPLORER'}


def load_dict():
    """Собирает словарь уже переведённых строк из выгрузки Weblate."""
    units = []
    for f in sorted(glob.glob(os.path.join(CACHE, '*-units.json'))):
        units += json.load(open(f))
    d = {}
    for u in units:
        if not u.get('translated'):
            continue
        s = (u.get('source') or [''])[0]
        t = (u.get('target') or [''])[0]
        if not s or not t or not t.strip():
            continue
        t = t.replace('\n[ADD]', '\n').replace('[ADD]', '')
        if s not in d:
            d[s] = t
    return units, d


def has_letters(s):
    """Есть ли в строке буквы помимо игровых тегов."""
    return bool(re.search(r'[A-Za-z]', TOKEN.sub('', s)))


def should_skip(s):
    """Пропускает имена файлов, идентификаторы и отладочные коды."""
    if s in SKIP_EXACT:
        return True
    if FILENAME.search(s):
        return True
    if CAMEL.fullmatch(s) and s != 'OuterNet':
        return True
    if IDENT.fullmatch(s):
        return True
    if FORMAT_ONLY.fullmatch(s):
        return True
    return False


def protect(s):
    """Заменяет игровые теги маркерами и запоминает пробелы вокруг них."""
    toks = []

    def rep(m):
        i = len(toks)
        start, end = m.start(), m.end()
        add_before = start > 0 and s[start - 1] not in ' \t\n'
        add_after = end < len(s) and s[end] not in ' \t\n'
        toks.append((m.group(0), add_before, add_after))
        return (' ' if add_before else '') + f'⟦XQ{i}QX⟧' + (' ' if add_after else '')

    return TOKEN.sub(rep, s), toks


def restore(s, toks):
    """Возвращает теги на место и убирает добавленные пробелы."""
    order = [int(m.group(1)) for m in MARK.finditer(s)]
    if order != list(range(len(toks))):
        raise ValueError(f'нарушен порядок маркеров: {order[:20]} из {len(toks)}')
    out = s
    for i, (_, add_before, add_after) in enumerate(toks):
        if add_before:
            out = re.sub(r'[ \t]*⟦XQ%dQX⟧' % i, f'⟦XQ{i}QX⟧', out, count=1)
        if add_after:
            out = re.sub(r'⟦XQ%dQX⟧[ \t]*' % i, f'⟦XQ{i}QX⟧', out, count=1)
    for i, (text, _, _) in enumerate(toks):
        out = out.replace(f'⟦XQ{i}QX⟧', text)
    if '⟦' in out or 'XQ' in out:
        raise ValueError('остался маркер')
    return out


def all_caps(s):
    """Проверяет, что исходная реплика написана капсом."""
    letters = [c for c in TOKEN.sub('', s) if c.isalpha()]
    return len(letters) >= 3 and all(c.isupper() for c in letters)


def fix_star_spacing(src, tr):
    """Восстанавливает пробел после звёздочки в начале реплики."""
    src_lines = src.split('\n')
    tr_lines = tr.split('\n')
    if len(src_lines) != len(tr_lines):
        return tr
    fixed = []
    for a, b in zip(src_lines, tr_lines):
        if re.search(r'\* ', a):
            # Добавляем пробел только после «звёздочки-маркера» реплики,
            # не задевая служебный тег {*} и другие звёздочки в тегах.
            b = re.sub(r'(?<!\{)\*(?=[A-Za-zА-Яа-яЁё])', '* ', b, count=1)
        fixed.append(b)
    return '\n'.join(fixed)


def request_batch(payload):
    """Отправляет пакет строк в Google Translate."""
    data = urllib.parse.urlencode([('q', p) for p in payload]).encode()
    req = urllib.request.Request(BASE, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    })
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def translate_payload(payload):
    """Переводит пакет с повторами при ошибках сети и лимитах."""
    last = None
    for attempt in range(7):
        try:
            res = request_batch(payload)
            if isinstance(res, dict) or not isinstance(res, list):
                raise ValueError('неожиданный тип ответа')
            if len(res) != len(payload):
                raise ValueError(f'не совпало число строк: {len(res)} != {len(payload)}')
            if not all(isinstance(x, str) for x in res):
                raise ValueError('перевод не является строкой')
            return res
        except Exception as e:
            last = e
            wait = min(90, 2 ** attempt) + random.random()
            print('повтор', attempt + 1, type(e).__name__, str(e)[:200], 'пауза', round(wait, 1), flush=True)
            time.sleep(wait)
    raise RuntimeError(f'пакет не переведён: {last}')


def translate_item(src):
    """Переводит одну строку (используется для строк с переносами)."""
    prot, toks = protect(src)
    tr = translate_payload([prot])[0]
    if all_caps(src):
        tr = tr.upper()
    tr = restore(tr, toks)
    tr = fix_star_spacing(src, tr)
    if not src[:1].isspace():
        tr = tr.lstrip(' ')
    if not src[-1:].isspace():
        tr = tr.rstrip(' ')
    if tr.count('\n') != src.count('\n'):
        lines = src.split('\n')
        out = []
        for line in lines:
            out.append(translate_item(line) if has_letters(line) else line)
        tr = '\n'.join(out)
    return tr


def batches(items, max_count=50, max_chars=3500):
    """Разбивает строки на пакеты по количеству и длине."""
    cur, chars = [], 0
    for it in items:
        n = len(it[2])
        if cur and (len(cur) >= max_count or chars + n > max_chars):
            yield cur
            cur, chars = [], 0
        cur.append(it)
        chars += n
    if cur:
        yield cur


def process_batch(batch):
    """Переводит один пакет строк в отдельном потоке.

    Возвращает два списка: успешные пары (исходник, перевод)
    и неудачные пары (исходник, описание ошибки).
    """
    payload = [p for _, p, _ in batch]
    try:
        res = translate_payload(payload)
    except Exception as e:
        return [], [(src, str(e)[:200]) for src, _, _ in batch]

    ok, bad = [], []
    for (src, _, toks), tr in zip(batch, res):
        try:
            if all_caps(src):
                tr = tr.upper()
            tr = restore(tr, toks)
            tr = fix_star_spacing(src, tr)
            if not src[:1].isspace():
                tr = tr.lstrip(' ')
            if not src[-1:].isspace():
                tr = tr.rstrip(' ')
            if tr.count('\n') != src.count('\n'):
                lines = src.split('\n')
                out = []
                for line in lines:
                    out.append(translate_item(line) if has_letters(line) else line)
                tr = '\n'.join(out)
            ok.append((src, tr))
        except Exception as e:
            bad.append((src, str(e)[:200]))
    return ok, bad


def save_progress(done, failed):
    """Атомарно сохраняет прогресс, чтобы можно было прервать перевод."""
    os.makedirs(CACHE, exist_ok=True)
    tmp = PROGRESS + '.tmp'
    with open(tmp, 'w') as f:
        json.dump({'done': done, 'failed': failed}, f, ensure_ascii=False)
    os.replace(tmp, PROGRESS)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'run'
    workers = 8
    if '--workers' in sys.argv:
        i = sys.argv.index('--workers')
        if i + 1 < len(sys.argv):
            workers = max(1, min(32, int(sys.argv[i + 1])))

    units, d = load_dict()
    all_src = list(dict.fromkeys((u.get('source') or [''])[0] for u in units))
    missing = [
        s for s in all_src
        if s and s not in d and has_letters(s) and len(s.strip()) > 1 and not should_skip(s)
    ]
    done = {}
    failed = {}
    if os.path.exists(PROGRESS):
        prog = json.load(open(PROGRESS))
        done = prog.get('done', {})
        failed = prog.get('failed', {})
    else:
        # Подхватываем уже выгруженный машинный перевод, чтобы не делать заново.
        exported = os.path.join(ROOT, 'src', 'machine-ru.json')
        if os.path.exists(exported):
            done = json.load(open(exported))
            print('подхвачено из src/machine-ru.json:', len(done), flush=True)
    todo = [s for s in missing if s not in done]
    print('не переведено', len(missing), 'готово', len(done), 'осталось', len(todo),
          'потоков', workers, flush=True)

    if mode == 'status':
        return
    if mode == 'sample':
        todo = todo[:120]

    prepared = []
    for s in todo:
        prot, toks = protect(s)
        prepared.append((s, prot, toks))
    queue = list(batches(prepared))
    print('пакетов', len(queue), flush=True)

    lock = threading.Lock()
    last_save = time.time()
    finished = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process_batch, b) for b in queue}
        for future in concurrent.futures.as_completed(futures):
            ok, bad = future.result()
            with lock:
                for src, tr in ok:
                    done[src] = tr
                for src, err in bad:
                    failed[src] = err
                    print('СТРОКА НЕ ПЕРЕВЕДЕНА', repr(src[:80]), err, flush=True)
                finished += 1
                now = time.time()
                # Пишем прогресс не чаще раза в 5 секунд, чтобы не тормозить потоки.
                if now - last_save >= 5 or finished == len(queue):
                    save_progress(done, failed)
                    last_save = now
                    print('прогресс', len(done), '/', len(missing),
                          'ошибок', len(failed), flush=True)

    save_progress(done, failed)

    if mode == 'sample':
        for s in todo[:60]:
            if s in done:
                print('ИСХОДНАЯ:', repr(s))
                print('ПЕРЕВОД :', repr(done[s]))
                print()
        print('пробных переведено:', sum(1 for s in todo if s in done),
              'ошибок:', sum(1 for s in todo if s in failed))


if __name__ == '__main__':
    main()

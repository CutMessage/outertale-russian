# Применяет к распакованному app.asar два патча:
# 1. разрешает mods:-протоколу загрузку шрифтов и ресурсов;
# 2. копирует встроенный мод из app.asar в пользовательскую папку mods.
#
# Использование:
#   python3 packaging/patch_game.py packaging/work/app

import os
import sys

PROTOCOL_OLD = "protocol.registerSchemesAsPrivileged([ { scheme: 'mods', privileges: { supportFetchAPI: true } } ]);"
PROTOCOL_NEW = "protocol.registerSchemesAsPrivileged([ { scheme: 'mods', privileges: { supportFetchAPI: true, corsEnabled: true, secure: true, stream: true } } ]);"

MOD_BLOCK = """});

((input, loop) => loop(input, loop))('mods', (input, loop) => {
   const path = `${__dirname}/${input}`;
   if (!existsSync(path)) {
      return;
   }
   const stat = statSync(path);
   if (stat.isFile()) {
      copyFileSync(path, join(spacetime, input));
   } else if (stat.isDirectory()) {
      mkdirSync(join(spacetime, input), { recursive: true });
      for (const name of readdirSync(path)) {
         loop(`${input}/${name}`, loop);
      }
   }
});

contextBridge.exposeInMainWorld('___spacetime___', {"""

ANCHOR = """});

contextBridge.exposeInMainWorld('___spacetime___', {"""


def patch_index(path):
    text = open(path).read()
    if PROTOCOL_NEW in text:
        print('index.js: патч протокола уже применён')
        return
    if PROTOCOL_OLD not in text:
        raise SystemExit('index.js: не найдена ожидаемая строка протокола — версия игры не 5.04?')
    open(path, 'w').write(text.replace(PROTOCOL_OLD, PROTOCOL_NEW, 1))
    print('index.js: патч протокола применён')


def patch_preload(path):
    text = open(path).read()
    if "loop(input, loop))('mods'" in text:
        print('preload.js: копирование мода уже добавлено')
        return
    if ANCHOR not in text:
        raise SystemExit('preload.js: не найдено место для вставки — версия игры не 5.04?')
    if 'existsSync' not in text:
        raise SystemExit('preload.js: не найден импорт existsSync')
    open(path, 'w').write(text.replace(ANCHOR, MOD_BLOCK, 1))
    print('preload.js: копирование мода добавлено')


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Использование: python3 packaging/patch_game.py <папка app>')
    app = sys.argv[1]
    patch_index(os.path.join(app, 'index.js'))
    patch_preload(os.path.join(app, 'preload.js'))


if __name__ == '__main__':
    main()

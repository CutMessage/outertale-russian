.PHONY: mod check zip clean

# Пересобрать мод из словарей
mod:
	python3 tools/build_mod.py

# Проверить, что сгенерированный мод соответствует исходникам
check:
	python3 tools/build_mod.py --check

# Собрать zip для ручной установки
zip: mod
	mkdir -p dist
	cd mods && zip -qr ../dist/outertale-ru-mod.zip ru_RU
	@echo "Готово: dist/outertale-ru-mod.zip"

clean:
	rm -rf dist cache packaging/work packaging/app.asar

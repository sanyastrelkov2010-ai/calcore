[app]

# Название вашего приложения
title = CalCore

# Имя пакета (должно быть уникальным)
package.name = calcore
package.domain = org.calcore

# Список исходных файлов (через запятую)
source.include_exts = py,png,jpg,kv,atlas,db

# Точка входа в приложение
source.main = main.py

# Версия приложения
version = 1.0

# Требуемые библиотеки (обязательно укажите kivy, kivymd и sqlite3 / python для БД)
requirements = python3,kivy==2.3.0,kivymd==1.1.1,pillow,sqlite3

# Ориентация экрана (portrait — портретная)
orientation = portrait

# Права доступа (например, для звука будильника или работы с файлами, если нужно)
# android.permissions = INTERNET

[buildozer]
# Уровень логирования
log_level = 2
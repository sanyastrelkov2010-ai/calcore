[app]
# Название приложения
title = CalCore

# Имя пакета
package.name = calcore
package.domain = org.calcore

# УКАЗЫВАЕМ ПАПКУ С ИСХОДНЫМ КОДОМ (Точка = текущая папка)
source.dir = .

# Какие файлы включать в сборку
source.include_exts = py,png,jpg,kv,atlas,db

# Главный файл запуска
source.main = main.py

# Версия
version = 1.0

# Необходимые зависимости
requirements = python3,kivy==2.3.0,kivymd==1.1.1,pillow,sqlite3

# Портретная ориентация экрана
orientation = portrait

# Автоматическое принятие лицензии Android
android.accept_sdk_license = True

[buildozer]
log_level = 2
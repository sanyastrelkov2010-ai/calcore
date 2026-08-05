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

# ИСПРАВЛЕНИЕ 1: Убрали sqlite3 (он встроен в Python, отдельное указание вызывает сбой)
requirements = python3,kivy==2.3.0,kivymd==1.1.1,pillow

# Портретная ориентация экрана
orientation = portrait

# ИСПРАВЛЕНИЕ 2: Жестко фиксируем стабильные версии Android API и NDK
android.api = 34
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
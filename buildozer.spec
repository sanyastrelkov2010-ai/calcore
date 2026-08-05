[app]
title = CalCore
package.name = calcore
package.domain = org.calcore
source.include_exts = py,png,jpg,kv,atlas,db
source.main = main.py
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.1.1,pillow,sqlite3
orientation = portrait

# АВТОМАТИЧЕСКОЕ ПРИНЯТИЕ ЛИЦЕНЗИИ ANDROID
android.accept_sdk_license = True

[buildozer]
log_level = 2
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.list import TwoLineListItem, OneLineListItem
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.uix.screenmanager import FadeTransition
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, StringProperty
from collections import defaultdict
from datetime import datetime, date, timedelta
import database

# Импорты для графиков
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Point

Window.size = (360, 740)

class SwipeableWeek(MDBoxLayout):
    touch_start_x = NumericProperty(0)
    touch_start_y = NumericProperty(0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_x = touch.x
            self.touch_start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and hasattr(self, 'touch_start_x'):
            diff_x = touch.x - self.touch_start_x
            diff_y = abs(touch.y - getattr(self, 'touch_start_y', touch.y))
            if abs(diff_x) > 50 and diff_y < 50: 
                app = MDApp.get_running_app()
                if diff_x > 0:
                    app.change_week(-1)
                else:
                    app.change_week(1)
                return True
        return super().on_touch_up(touch)

class WeightChart(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.history = []

    def update_canvas(self, *args):
        self.canvas.clear()
        if not self.history: return
        weights = [row[1] for row in self.history]
        if len(weights) < 1: return
        
        min_w = min(weights) - 1
        max_w = max(weights) + 1
        diff = max_w - min_w
        if diff == 0: diff = 1
        
        with self.canvas:
            Color(1, 0.6, 0.2, 1)
            points = []
            step_x = self.width / max(1, len(weights) - 1)
            for i, w in enumerate(weights):
                x = self.x + i * step_x
                norm_y = (w - min_w) / diff
                y = self.y + norm_y * self.height
                points.extend([x, y])
            
            if len(points) >= 4:
                Line(points=points, width=dp(2))
            if len(points) >= 2:
                Point(points=points, pointsize=dp(4))

KV = '''
<ClickableRow@ButtonBehavior+MDBoxLayout>:
    ripple_behavior: True

<StatBlock@ButtonBehavior+MDBoxLayout>:
    orientation: "vertical"
    adaptive_height: True
    spacing: dp(2)
    value: 0
    max_value: 100
    ring_color: 0.4, 0.8, 0.6, 1
    title: "Title"
    unit: "unit"
    consumed_text: "съед: 0"
    ripple_behavior: False
    
    MDFloatLayout:
        size_hint: None, None
        size: dp(85), dp(85)
        pos_hint: {"center_x": .5}
        canvas.before:
            Color:
                rgba: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (0.9, 0.9, 0.9, 1)
            Line:
                circle: (self.center_x, self.center_y, dp(38))
                width: dp(4)
            Color:
                rgba: root.ring_color
            Line:
                circle: (self.center_x, self.center_y, dp(38), 0, min((root.value / root.max_value * 360), 360) if root.max_value > 0 else 0)
                width: dp(4)
        
        MDLabel:
            text: str(int(max(0, root.max_value - root.value)))
            font_size: "18sp"
            bold: True
            halign: "center"
            pos_hint: {"center_x": .5, "center_y": .5}
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
            
        MDLabel:
            text: f"{root.title}\\n{root.unit}"
            halign: "center"
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.5, 0.5, 0.5, 1)
            font_size: "9sp"
            line_height: 0.9
            pos_hint: {"center_x": .5, "center_y": .22}
                
    MDLabel:
        text: root.consumed_text
        font_style: "Caption"
        halign: "center"
        font_size: "10sp"
        theme_text_color: "Custom"
        text_color: (0.8, 0.8, 0.8, 1) if app.theme_cls.theme_style == "Dark" else (0.4, 0.4, 0.4, 1)
        adaptive_height: True

<SemiTimer@MDFloatLayout>:
    value: 0
    max_value: 100
    text: "00:00"
    color: 0.4, 0.8, 0.6, 1
    size_hint_y: None
    height: dp(100)
    canvas.before:
        Color:
            rgba: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (0.9, 0.9, 0.9, 1)
        Line:
            circle: (self.center_x, self.center_y, dp(40), -120, 120)
            width: dp(4)
            cap: "round"
        Color:
            rgba: root.color
        Line:
            circle: (self.center_x, self.center_y, dp(40), -120, -120 + (root.value / root.max_value * 240) if root.max_value > 0 else -120)
            width: dp(4)
            cap: "round"
    MDLabel:
        text: root.text
        font_style: "H5"
        bold: True
        halign: "center"
        pos_hint: {"center_x": .5, "center_y": .5}
        theme_text_color: "Custom"
        text_color: root.color

<ProgressCard>:
    orientation: "vertical"
    padding: [dp(10), dp(2), dp(10), dp(10)]
    radius: [dp(20)]
    md_bg_color: (0.18, 0.18, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
    elevation: 0
    adaptive_height: True
    
    MDLabel:
        text: root.date_text
        font_style: "Subtitle1"
        bold: True
        halign: "center"
        adaptive_height: True
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
        
    Widget:
        size_hint_y: None
        height: dp(2)
        
    MDGridLayout:
        cols: 3
        spacing: dp(10)
        adaptive_height: True
        
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(8)
            adaptive_height: True
            StatBlock:
                title: "белки"
                unit: "г"
                ring_color: 1, 0.6, 0.4, 1
                value: root.p_val
                max_value: root.p_max
                consumed_text: f"съед: {int(root.p_val)}г"
            StatBlock:
                title: "вода"
                unit: "мл"
                ring_color: 0.2, 0.6, 1, 1
                value: root.water_val
                max_value: root.water_max
                consumed_text: f"съед: {int(root.water_val)}мл"
                ripple_behavior: True
                on_release: app.add_water(250)
            
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            Widget:
                size_hint_y: None
                height: dp(42)
            StatBlock:
                title: "ККАЛ"
                unit: ""
                ring_color: 0.4, 0.8, 0.6, 1
                value: root.cal_val
                max_value: root.cal_max
                consumed_text: f"съед: {int(root.cal_val)}г"
            Widget:
                size_hint_y: None
                height: dp(42)
            
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(8)
            adaptive_height: True
            StatBlock:
                title: "жиры, г"
                unit: ""
                ring_color: 1, 0.7, 0.2, 1
                value: root.f_val
                max_value: root.f_max
                consumed_text: f"съед: {int(root.f_val)}г"
            StatBlock:
                title: "углеводы, г"
                unit: ""
                ring_color: 0.3, 0.7, 0.9, 1
                value: root.c_val
                max_value: root.c_max
                consumed_text: f"съед: {int(root.c_val)}г"

<PersonalDataContent>:
    orientation: "vertical"
    spacing: dp(12)
    size_hint_y: None
    height: dp(320)
    MDTextField:
        id: name_field
        hint_text: "Ваше имя и фамилия"
        icon_left: "account"
    MDTextField:
        id: age_field
        hint_text: "Возраст"
        input_filter: "int"
        icon_left: "calendar"
    MDTextField:
        id: weight_field
        hint_text: "Вес (кг)"
        input_filter: "float"
        icon_left: "weight"
    MDTextField:
        id: height_field
        hint_text: "Рост (см)"
        input_filter: "float"
        icon_left: "human-male-height"
    MDBoxLayout:
        orientation: "horizontal"
        adaptive_height: True
        spacing: dp(5)
        MDLabel:
            text: "Пол:"
            size_hint_x: None
            width: dp(40)
            font_style: "Body2"
            theme_text_color: "Hint"
        MDCheckbox:
            id: check_male
            group: "gender"
            size_hint: None, None
            size: dp(48), dp(48)
            pos_hint: {"center_y": .5}
        MDLabel:
            text: "Мужской"
            font_style: "Body2"
            pos_hint: {"center_y": .5}
        MDCheckbox:
            id: check_female
            group: "gender"
            size_hint: None, None
            size: dp(48), dp(48)
            pos_hint: {"center_y": .5}
        MDLabel:
            text: "Женский"
            font_style: "Body2"
            pos_hint: {"center_y": .5}

<GoalsDataContent>:
    orientation: "vertical"
    spacing: dp(12)
    size_hint_y: None
    height: dp(260)
    MDTextField:
        id: cal_field
        hint_text: "Норма Калорий (ккал)"
        input_filter: "int"
        icon_left: "fire"
    MDTextField:
        id: p_field
        hint_text: "Норма Белков (г)"
        input_filter: "int"
    MDTextField:
        id: f_field
        hint_text: "Норма Жиров (г)"
        input_filter: "int"
    MDTextField:
        id: c_field
        hint_text: "Норма Углеводов (г)"
        input_filter: "int"

<FoodSelectorContent>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(450)
    spacing: dp(10)
    MDTextField:
        id: search_field
        hint_text: "Поиск блюда..."
        icon_left: "magnify"
        on_text: app.filter_food_list(self.text)
    MDScrollView:
        MDList:
            id: food_list

<DayCard@MDCard>:
    size_hint_y: None
    height: dp(65)
    orientation: "vertical"
    padding: dp(5)
    elevation: 0
    date_str: ""
    day_name: ""
    day_num: ""
    md_bg_color: (0.2, 0.2, 0.2, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
    on_release: app.select_workout_date(self.date_str)
    MDLabel:
        text: root.day_name
        halign: "center"
        font_style: "Caption"
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if root.md_bg_color == [0.4, 0.8, 0.6, 1.0] else ((0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.4, 0.4, 0.4, 1))
    MDLabel:
        text: root.day_num
        halign: "center"
        font_style: "H6"
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if root.md_bg_color == [0.4, 0.8, 0.6, 1.0] else ((1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1))

<SwipeableWeek>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(65)
    spacing: dp(5)

MDFloatLayout:
    md_bg_color: (0.12, 0.12, 0.12, 1) if app.theme_cls.theme_style == "Dark" else (245/255, 250/255, 245/255, 1)

    MDScreenManager:
        id: sm
        md_bg_color: (0.12, 0.12, 0.12, 1) if app.theme_cls.theme_style == "Dark" else (245/255, 250/255, 245/255, 1)
        
        MainScreen:
            name: "main"
        WorkoutsScreen:
            name: "workouts"
        StatisticsScreen:
            name: "statistics"
        ProfileScreen:
            name: "profile"

    # --- Кастомное нижнее меню ---
    MDCard:
        size_hint_y: None
        height: dp(65)
        pos_hint: {"bottom": 1}
        radius: [dp(25), dp(25), 0, 0]
        md_bg_color: (0.18, 0.18, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
        elevation: 0
        
        MDBoxLayout:
            orientation: "horizontal"
            padding: [dp(10), 0, dp(10), 0]
            
            MDBoxLayout:
                orientation: "vertical"
                MDIconButton:
                    icon: "home"
                    theme_icon_color: "Custom"
                    icon_color: (0.4, 0.8, 0.6, 1) if sm.current == "main" else (0.6, 0.6, 0.6, 1)
                    pos_hint: {"center_x": .5, "center_y": .6}
                    on_release: app.switch_screen("main")
                MDLabel:
                    text: "Главная"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: (0.4, 0.8, 0.6, 1) if sm.current == "main" else ((0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.6, 0.6, 0.6, 1))
            
            MDBoxLayout:
                orientation: "vertical"
                MDIconButton:
                    icon: "dumbbell"
                    theme_icon_color: "Custom"
                    icon_color: (0.4, 0.8, 0.6, 1) if sm.current == "workouts" else (0.6, 0.6, 0.6, 1)
                    pos_hint: {"center_x": .5, "center_y": .6}
                    on_release: app.switch_screen("workouts")
                MDLabel:
                    text: "Тренировки"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: (0.4, 0.8, 0.6, 1) if sm.current == "workouts" else ((0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.6, 0.6, 0.6, 1))
            
            Widget:
                size_hint_x: 0.8
                
            MDBoxLayout:
                orientation: "vertical"
                MDIconButton:
                    icon: "chart-bar"
                    theme_icon_color: "Custom"
                    icon_color: (0.4, 0.8, 0.6, 1) if sm.current == "statistics" else (0.6, 0.6, 0.6, 1)
                    pos_hint: {"center_x": .5, "center_y": .6}
                    on_release: app.switch_screen("statistics")
                MDLabel:
                    text: "Статистика"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: (0.4, 0.8, 0.6, 1) if sm.current == "statistics" else ((0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.6, 0.6, 0.6, 1))
                    
            MDBoxLayout:
                orientation: "vertical"
                MDIconButton:
                    icon: "account-outline"
                    theme_icon_color: "Custom"
                    icon_color: (0.4, 0.8, 0.6, 1) if sm.current == "profile" else (0.6, 0.6, 0.6, 1)
                    pos_hint: {"center_x": .5, "center_y": .6}
                    on_release: app.switch_screen("profile")
                MDLabel:
                    text: "Профиль"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: (0.4, 0.8, 0.6, 1) if sm.current == "profile" else ((0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.6, 0.6, 0.6, 1))

    MDFloatingActionButton:
        icon: "plus"
        md_bg_color: 255/255, 154/255, 118/255, 1
        theme_icon_color: "Custom"
        icon_color: 1, 1, 1, 1
        pos_hint: {"center_x": .5}
        y: dp(25)
        elevation: 0
        on_release: app.show_food_dialog()

# ================= ЭКРАН 1: ГЛАВНАЯ =================
<MainScreen>:
    md_bg_color: (0.12, 0.12, 0.12, 1) if app.theme_cls.theme_style == "Dark" else (245/255, 250/255, 245/255, 1)
    on_enter: app.schedule_update_meals()

    MDBoxLayout:
        orientation: "vertical"
        # Увеличен верхний отступ (padding), чтобы опустить аватарку и шапку ниже
        padding: [dp(20), dp(25), dp(20), 0]
        spacing: dp(10)
        
        MDBoxLayout:
            size_hint_y: None
            height: dp(45)
            spacing: dp(10)
            
            MDIconButton:
                id: main_avatar
                icon: "face-woman"
                theme_icon_color: "Custom"
                icon_color: (0.9, 0.9, 0.9, 1) if app.theme_cls.theme_style == "Dark" else (0.3, 0.3, 0.3, 1)
                md_bg_color: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (220/255, 230/255, 220/255, 1)
                user_font_size: "32sp"
                on_release: app.switch_screen("profile")
                
            MDBoxLayout:
                orientation: "vertical"
                pos_hint: {"center_y": .5}
                MDLabel:
                    id: main_name_label
                    text: "Привет!"
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                MDLabel:
                    id: current_datetime_label
                    text: "Загрузка времени..."
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: (0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.5, 0.5, 0.5, 1)
                    
            MDIconButton:
                icon: "bell-outline"
                theme_icon_color: "Custom"
                icon_color: (0.9, 0.9, 0.9, 1) if app.theme_cls.theme_style == "Dark" else (0.2, 0.2, 0.2, 1)
        
        ProgressCard:
            id: main_progress_card
            date_text: "Дневной Прогресс"
        
        MDLabel:
            text: "Приемы Пищи (Сегодня)"
            font_style: "Subtitle1"
            bold: True
            adaptive_height: True
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
            
        MDScrollView:
            shows_vertical_scroll_indicator: False
            MDBoxLayout:
                id: meals_container
                orientation: "vertical"
                spacing: dp(15)
                padding: [0, 0, 0, dp(100)]
                adaptive_height: True

# ================= ЭКРАН 2: ТРЕНИРОВКИ =================
<WorkoutsScreen>:
    md_bg_color: (0.12, 0.12, 0.12, 1) if app.theme_cls.theme_style == "Dark" else (245/255, 250/255, 245/255, 1)
    on_enter: app.schedule_setup_calendar()

    MDBoxLayout:
        orientation: "vertical"
        padding: [dp(15), dp(20), dp(15), 0]
        spacing: dp(10)
        
        MDLabel:
            text: "План тренировок"
            font_style: "H6"
            bold: True
            adaptive_height: True
            halign: "center"
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
            
        SwipeableWeek:
            id: days_container
            
        MDLabel:
            id: selected_date_label
            text: "План на день"
            font_style: "Subtitle1"
            theme_text_color: "Custom"
            text_color: (0.8, 0.8, 0.8, 1) if app.theme_cls.theme_style == "Dark" else (0.4, 0.4, 0.4, 1)
            adaptive_height: True
            
        MDScrollView:
            shows_vertical_scroll_indicator: False
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(15)
                adaptive_height: True
                padding: [0, 0, 0, dp(10)]
                    
                MDTextField:
                    id: workout_note
                    hint_text: "Запишите свой план здесь..."
                    multiline: True
                    mode: "rectangle"
                    size_hint_y: None
                    height: dp(150)
                    text_color_normal: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0, 0, 0, 1)
                    hint_text_color_normal: (0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.5, 0.5, 0.5, 1)
                    
                MDFlatButton:
                    text: "СОХРАНИТЬ ПЛАН"
                    theme_text_color: "Custom"
                    text_color: 0.4, 0.8, 0.6, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.save_workout_plan()

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(160)
            spacing: dp(10)
            
            MDCard:
                orientation: "vertical"
                padding: dp(10)
                radius: [dp(15)]
                md_bg_color: (0.18, 0.18, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
                elevation: 0
                
                MDLabel:
                    text: "Секундомер"
                    font_style: "Caption"
                    halign: "center"
                    adaptive_height: True
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                    
                SemiTimer:
                    value: app.stopwatch_time % 60 if app.stopwatch_time > 0 else 0
                    max_value: 60
                    text: app.stopwatch_text
                    color: 1, 0.6, 0.2, 1
                    
                MDBoxLayout:
                    orientation: "horizontal"
                    adaptive_height: True
                    spacing: dp(5)
                    pos_hint: {"center_x": .5}
                    adaptive_width: True
                    
                    MDIconButton:
                        icon: "refresh"
                        icon_size: "18sp"
                        md_bg_color: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.95, 1)
                        theme_icon_color: "Custom"
                        icon_color: (0.8, 0.8, 0.8, 1) if app.theme_cls.theme_style == "Dark" else (0.5, 0.5, 0.5, 1)
                        on_release: app.reset_stopwatch()
                    MDIconButton:
                        icon: "play-pause"
                        icon_size: "24sp"
                        theme_icon_color: "Custom"
                        icon_color: 1, 0.6, 0.2, 1
                        on_release: app.toggle_stopwatch()

            Widget:
                size_hint_x: None
                width: dp(55)

            MDCard:
                orientation: "vertical"
                padding: dp(10)
                radius: [dp(15)]
                md_bg_color: (0.18, 0.18, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
                elevation: 0
                
                MDLabel:
                    text: "Таймер"
                    font_style: "Caption"
                    halign: "center"
                    adaptive_height: True
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                    
                SemiTimer:
                    value: app.timer_time
                    max_value: app.timer_max
                    text: app.timer_text
                    color: 0.4, 0.8, 0.6, 1
                    
                MDBoxLayout:
                    orientation: "horizontal"
                    adaptive_height: True
                    spacing: 0
                    pos_hint: {"center_x": .5}
                    adaptive_width: True
                    
                    MDIconButton:
                        icon: "minus"
                        icon_size: "16sp"
                        md_bg_color: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.95, 1)
                        theme_icon_color: "Custom"
                        icon_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0, 0, 0, 1)
                        on_release: app.add_timer_time(-60)
                    MDIconButton:
                        icon: "refresh"
                        icon_size: "18sp"
                        md_bg_color: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.95, 1)
                        theme_icon_color: "Custom"
                        icon_color: (0.8, 0.8, 0.8, 1) if app.theme_cls.theme_style == "Dark" else (0.5, 0.5, 0.5, 1)
                        on_release: app.reset_timer()
                    MDIconButton:
                        icon: "play-pause"
                        icon_size: "24sp"
                        theme_icon_color: "Custom"
                        icon_color: 0.4, 0.8, 0.6, 1
                        on_release: app.toggle_timer()
                    MDIconButton:
                        icon: "plus"
                        icon_size: "16sp"
                        md_bg_color: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.95, 1)
                        theme_icon_color: "Custom"
                        icon_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0, 0, 0, 1)
                        on_release: app.add_timer_time(60)

        Widget:
            size_hint_y: None
            height: dp(65)

# ================= ЭКРАН 3: СТАТИСТИКА =================
<StatisticsScreen>:
    md_bg_color: (0.12, 0.12, 0.12, 1) if app.theme_cls.theme_style == "Dark" else (245/255, 250/255, 245/255, 1)
    on_enter: app.schedule_setup_statistics()
    
    MDBoxLayout:
        orientation: "vertical"
        padding: [dp(20), dp(20), dp(20), dp(85)]
        spacing: dp(15)
        
        MDBoxLayout:
            size_hint_y: None
            height: dp(50)
            MDLabel:
                text: "Статистика"
                font_style: "H6"
                bold: True
                halign: "center"
                valign: "middle"
                theme_text_color: "Custom"
                text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                
        Carousel:
            id: stats_carousel
            direction: "right"
            size_hint_y: None
            height: dp(260)
            
        MDLabel:
            text: "График веса (за 30 дней)"
            font_style: "Subtitle1"
            bold: True
            adaptive_height: True
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
            
        MDCard:
            orientation: "vertical"
            padding: dp(15)
            spacing: dp(10)
            radius: [dp(20)]
            md_bg_color: (0.18, 0.18, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
            elevation: 0
            size_hint_y: 1
            
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(10)
                adaptive_height: True
                MDTextField:
                    id: weight_input
                    hint_text: "Ваш вес (кг)"
                    input_filter: "float"
                    size_hint_x: 0.6
                    text_color_normal: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0, 0, 0, 1)
                    hint_text_color_normal: (0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == "Dark" else (0.5, 0.5, 0.5, 1)
                MDRaisedButton:
                    text: "Записать"
                    md_bg_color: 0.4, 0.8, 0.6, 1
                    elevation: 0
                    size_hint_x: 0.4
                    on_release: app.save_weight()
                    
            WeightChart:
                id: weight_chart
                size_hint_y: 1

# ================= ЭКРАН 4: ПРОФИЛЬ =================
<ProfileScreen>:
    md_bg_color: (0.12, 0.12, 0.12, 1) if app.theme_cls.theme_style == "Dark" else (245/255, 250/255, 245/255, 1)
    MDFloatLayout:
        canvas.before:
            Color:
                rgba: (0.18, 0.22, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (215/255, 240/255, 225/255, 1)
            RoundedRectangle:
                pos: 0, root.height - dp(240)
                size: root.width, dp(240)
                radius: [0, 0, dp(120), dp(40)]

        MDBoxLayout:
            orientation: "vertical"
            pos_hint: {"top": 1}
            # Увеличен верхний отступ для профиля
            padding: [dp(20), dp(45), dp(20), 0]
            spacing: dp(10)

            MDLabel:
                text: "Мой Профиль"
                font_style: "H6"
                bold: True
                halign: "center"
                adaptive_height: True
                theme_text_color: "Custom"
                text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)

            MDFloatLayout:
                size_hint: None, None
                size: dp(110), dp(110)
                pos_hint: {"center_x": .5}
                
                canvas.before:
                    Color:
                        rgba: 0.4, 0.8, 0.6, 1
                    Line:
                        circle: (self.center_x, self.center_y, dp(48))
                        width: dp(2.5)
                    Color:
                        rgba: 1, 0.6, 0.2, 1
                    Line:
                        circle: (self.center_x, self.center_y, dp(54))
                        width: dp(2.5)

                MDIconButton:
                    id: profile_avatar
                    icon: "face-woman"
                    icon_size: "60sp"
                    pos_hint: {"center_x": .5, "center_y": .5}
                    md_bg_color: (0.25, 0.25, 0.25, 1) if app.theme_cls.theme_style == "Dark" else (235/255, 230/255, 225/255, 1)
                    
            MDLabel:
                id: profile_name_label
                text: "Пользователь"
                font_style: "H5"
                bold: True
                halign: "center"
                adaptive_height: True
                theme_text_color: "Custom"
                text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(5)
                adaptive_height: True
                
                MDLabel:
                    text: "Настройки"
                    font_style: "Subtitle1"
                    bold: True
                    adaptive_height: True
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                    
                Widget:
                    size_hint_y: None
                    # Еще больше увеличили отступ, чтобы опустить кнопки в профиле ниже
                    height: dp(150) 
                    
                MDCard:
                    orientation: "vertical"
                    md_bg_color: (0.18, 0.18, 0.18, 1) if app.theme_cls.theme_style == "Dark" else (1, 1, 1, 1)
                    radius: [dp(15)]
                    adaptive_height: True
                    elevation: 0
                    
                    ClickableRow:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(50)
                        padding: [dp(15), 0, dp(15), 0]
                        spacing: dp(15)
                        on_release: app.show_personal_data_dialog()
                        
                        MDIcon:
                            icon: "account-outline"
                            theme_text_color: "Custom"
                            text_color: 0.4, 0.8, 0.6, 1
                            pos_hint: {"center_y": .5}
                            
                        MDLabel:
                            text: "Личные Данные"
                            pos_hint: {"center_y": .5}
                            theme_text_color: "Custom"
                            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                            
                        MDIcon:
                            icon: "chevron-right"
                            theme_text_color: "Hint"
                            pos_hint: {"center_y": .5}
                            
                    MDSeparator:
                        
                    ClickableRow:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(50)
                        padding: [dp(15), 0, dp(15), 0]
                        spacing: dp(15)
                        on_release: app.show_goals_dialog()
                        
                        MDIcon:
                            icon: "bullseye-arrow"
                            theme_text_color: "Custom"
                            text_color: 1, 0.6, 0.2, 1
                            pos_hint: {"center_y": .5}
                            
                        MDLabel:
                            text: "Мои цели (КБЖУ)"
                            pos_hint: {"center_y": .5}
                            theme_text_color: "Custom"
                            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                            
                        MDIcon:
                            icon: "chevron-right"
                            theme_text_color: "Hint"
                            pos_hint: {"center_y": .5}

                    MDSeparator:

                    ClickableRow:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(50)
                        padding: [dp(15), 0, dp(15), 0]
                        spacing: dp(15)
                        on_release: app.toggle_theme()
                        
                        MDIcon:
                            icon: "theme-dark-light"
                            theme_text_color: "Custom"
                            text_color: 0.4, 0.8, 0.6, 1
                            pos_hint: {"center_y": .5}
                            
                        MDLabel:
                            text: "Темная тема"
                            pos_hint: {"center_y": .5}
                            theme_text_color: "Custom"
                            text_color: (1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0.1, 0.1, 0.1, 1)
                            
                        MDLabel:
                            id: theme_status_label
                            text: "Вкл" if app.theme_cls.theme_style == "Dark" else "Выкл"
                            halign: "right"
                            theme_text_color: "Hint"
                            pos_hint: {"center_y": .5}
            Widget:
'''

class ProgressCard(MDCard):
    date_text = StringProperty("Сегодня")
    cal_val = NumericProperty(0)
    cal_max = NumericProperty(2000)
    rem_cal = NumericProperty(0)
    cons_cal = NumericProperty(0)
    
    p_val = NumericProperty(0)
    p_max = NumericProperty(150)
    rem_p = NumericProperty(0)
    
    f_val = NumericProperty(0)
    f_max = NumericProperty(70)
    rem_f = NumericProperty(0)
    
    c_val = NumericProperty(0)
    c_max = NumericProperty(200)
    rem_c = NumericProperty(0)
    
    water_val = NumericProperty(0)
    water_max = NumericProperty(2000)

class PersonalDataContent(MDBoxLayout): pass
class GoalsDataContent(MDBoxLayout): pass
class FoodSelectorContent(MDBoxLayout): pass
class MainScreen(MDScreen): pass
class WorkoutsScreen(MDScreen): pass
class StatisticsScreen(MDScreen): pass
class ProfileScreen(MDScreen): pass

class CalCoreApp(MDApp):
    dialog = None
    goals_dialog = None
    food_dialog = None
    user_data = {}
    all_foods = []
    expanded_categories = set()
    
    week_offset = 0
    selected_workout_date = None

    stopwatch_time = NumericProperty(0.0)
    stopwatch_text = StringProperty("00:00.0")
    stopwatch_running = False
    
    timer_max = NumericProperty(300.0)
    timer_time = NumericProperty(300.0) 
    timer_text = StringProperty("05:00")
    timer_running = False
    
    alarm_sound = None

    def build(self):
        database.init_db()
        self.theme_cls.theme_style = database.get_theme_setting()
        self.user_data = database.get_user_data()
        self.all_foods = database.get_all_foods()
        
        self.alarm_sound = SoundLoader.load('alarm.wav')
        
        self.root_widget = Builder.load_string(KV)
        self.root_widget.ids.sm.transition = FadeTransition(duration=0.15)
        Clock.schedule_interval(self.tick_clock, 0.1)
        
        return self.root_widget
        
    def on_start(self):
        self.update_ui_with_user_data()
        self.refresh_dashboard()

    def switch_screen(self, screen_name):
        self.root_widget.ids.sm.current = screen_name

    def toggle_theme(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"
        
        database.save_theme_setting(self.theme_cls.theme_style)
        self.refresh_dashboard()

    def add_water(self, amount):
        database.add_water(amount)
        self.refresh_dashboard()

    def tick_clock(self, dt):
        now = datetime.now()
        days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        months_ru = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
        
        date_str = f"{days_ru[now.weekday()]}, {now.day} {months_ru[now.month - 1]}"
        time_str = now.strftime("%H:%M")
        
        main_screen = self.root_widget.ids.sm.get_screen("main")
        main_screen.ids.current_datetime_label.text = f"{date_str} | {time_str}"

        if self.stopwatch_running:
            self.stopwatch_time += dt
            m, s = divmod(int(self.stopwatch_time), 60)
            ms = int((self.stopwatch_time - int(self.stopwatch_time)) * 10)
            self.stopwatch_text = f"{m:02d}:{s:02d}.{ms}"

        if self.timer_running:
            if self.timer_time > 0:
                self.timer_time -= dt
                if self.timer_time <= 0:
                    self.timer_time = 0
                    self.timer_running = False
                    if self.alarm_sound: self.alarm_sound.play()
            m, s = divmod(int(self.timer_time), 60)
            self.timer_text = f"{m:02d}:{s:02d}"

    def toggle_stopwatch(self): self.stopwatch_running = not self.stopwatch_running
    def reset_stopwatch(self):
        self.stopwatch_running = False
        self.stopwatch_time = 0.0
        self.stopwatch_text = "00:00.0"

    def toggle_timer(self):
        if self.timer_time > 0: self.timer_running = not self.timer_running
    def reset_timer(self):
        self.timer_running = False
        self.timer_time = self.timer_max
        m, s = divmod(int(self.timer_time), 60)
        self.timer_text = f"{m:02d}:{s:02d}"
        
    def add_timer_time(self, seconds):
        self.timer_max = max(60, self.timer_max + seconds)
        self.timer_time = self.timer_max
        self.timer_running = False
        m, s = divmod(int(self.timer_time), 60)
        self.timer_text = f"{m:02d}:{s:02d}"

    def refresh_dashboard(self):
        goals = database.get_daily_goals()
        consumed = database.get_consumed_today()
        water = database.get_water_today()
        
        main_screen = self.root_widget.ids.sm.get_screen("main")
        card = main_screen.ids.main_progress_card
        
        card.cal_max = goals[0]
        card.cal_val = consumed[0]
        card.rem_cal = max(0, goals[0] - consumed[0])
        card.cons_cal = consumed[0]
        card.p_max = goals[1]
        card.p_val = consumed[1]
        card.rem_p = max(0, goals[1] - consumed[1])
        card.f_max = goals[2]
        card.f_val = consumed[2]
        card.rem_f = max(0, goals[2] - consumed[2])
        card.c_max = goals[3]
        card.c_val = consumed[3]
        card.rem_c = max(0, goals[3] - consumed[3])
        card.water_val = water
        card.water_max = 2000

    def schedule_update_meals(self):
        Clock.schedule_once(lambda dt: self.update_meals_ui(), 0.05)

    def update_meals_ui(self):
        main_screen = self.root_widget.ids.sm.get_screen("main")
        container = main_screen.ids.meals_container
        container.clear_widgets()
        
        meals = database.get_todays_meals()
        mint_color = (130/255, 210/255, 185/255, 1)
        orange_color = (255/255, 160/255, 115/255, 1)

        for index, meal in enumerate(meals):
            meal_id, food_name, calories = meal
            bg_color = mint_color if index % 2 == 0 else orange_color
            icon_name = "bowl-mix" if index % 2 == 0 else "food-drumstick"
            
            card = MDCard(size_hint_y=None, height=dp(80), padding=dp(10), spacing=dp(15), radius=[dp(20)], md_bg_color=bg_color, elevation=0)
            icon = MDIconButton(icon=icon_name, md_bg_color=(1, 1, 1, 0.5), pos_hint={"center_y": .5})
            text_box = MDBoxLayout(orientation="vertical", pos_hint={"center_y": .5})
            text_box.add_widget(MDLabel(text="Прием пищи", color=(1, 1, 1, 1), bold=True, font_style="Subtitle2"))
            text_box.add_widget(MDLabel(text=f"{food_name}\n{calories:.0f} ккал", color=(1, 1, 1, 0.9), font_style="Caption"))
            
            del_btn = MDIconButton(
                icon="trash-can-outline", theme_icon_color="Custom", icon_color=(0.9, 0.2, 0.2, 1),
                md_bg_color=(1, 1, 1, 0.7), pos_hint={"center_y": .5},
                on_release=lambda x, m_id=meal_id: self.delete_meal_action(m_id)
            )
            card.add_widget(icon)
            card.add_widget(text_box)
            card.add_widget(del_btn)
            container.add_widget(card)

    def delete_meal_action(self, meal_id):
        database.delete_meal(meal_id)
        self.refresh_dashboard()
        self.update_meals_ui()

    def schedule_setup_statistics(self):
        Clock.schedule_once(lambda dt: self.setup_statistics(), 0.05)

    def setup_statistics(self):
        screen = self.root_widget.ids.sm.get_screen("statistics")
        carousel = screen.ids.stats_carousel
        if len(carousel.slides) == 0:
            goals = database.get_daily_goals()
            today = date.today()
            
            for i in range(6, -1, -1):
                target_date = today - timedelta(days=i)
                consumed = database.get_consumed_today(target_date.isoformat())
                water = database.get_water_today(target_date.isoformat())
                
                card = ProgressCard()
                card.date_text = "Сегодня" if i == 0 else target_date.strftime("%d.%m.%Y")
                
                card.cal_max = goals[0]
                card.cal_val = consumed[0]
                card.rem_cal = max(0, goals[0] - consumed[0])
                card.cons_cal = consumed[0]
                card.p_max = goals[1]
                card.p_val = consumed[1]
                card.rem_p = max(0, goals[1] - consumed[1])
                card.f_max = goals[2]
                card.f_val = consumed[2]
                card.rem_f = max(0, goals[2] - consumed[2])
                card.c_max = goals[3]
                card.c_val = consumed[3]
                card.rem_c = max(0, goals[3] - consumed[3])
                card.water_val = water
                card.water_max = 2000
                
                wrap = MDBoxLayout(padding=[0, 0, 0, 0])
                wrap.add_widget(card)
                carousel.add_widget(wrap)
                
            carousel.index = 6
        self.update_weight_chart()

    def save_weight(self):
        screen = self.root_widget.ids.sm.get_screen("statistics")
        w_text = screen.ids.weight_input.text
        if w_text:
            database.add_weight_log(float(w_text))
            self.update_weight_chart()
            screen.ids.weight_input.text = ""

    def update_weight_chart(self):
        history = database.get_weight_history(30)
        screen = self.root_widget.ids.sm.get_screen("statistics")
        chart = screen.ids.weight_chart
        chart.history = history
        chart.update_canvas()

    def show_food_dialog(self):
        if not self.food_dialog:
            self.food_dialog = MDDialog(
                title="Добавить прием пищи", type="custom", content_cls=FoodSelectorContent(),
                buttons=[MDFlatButton(text="ЗАКРЫТЬ", theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), on_release=lambda x: self.food_dialog.dismiss())],
            )
        self.food_dialog.content_cls.ids.search_field.text = ""
        self.expanded_categories.clear() 
        self.filter_food_list("") 
        self.food_dialog.open()

    def filter_food_list(self, query):
        list_container = self.food_dialog.content_cls.ids.food_list
        list_container.clear_widgets()
        query = query.lower()
        
        categorized_foods = defaultdict(list)
        for f in self.all_foods:
            if query in f[1].lower(): categorized_foods[f[2]].append(f)
        
        for cat, foods in categorized_foods.items():
            is_expanded = (cat in self.expanded_categories) or bool(query)
            arrow = "▲" if is_expanded else "▼"
            
            header = OneLineListItem(
                text=f"{arrow} [b]{cat.upper()}[/b]", theme_text_color="Custom", text_color=(0.4, 0.8, 0.6, 1),
                on_release=lambda x, c=cat: self.toggle_category(c)
            )
            header.ids._lbl_primary.markup = True
            list_container.add_widget(header)
            
            if is_expanded:
                for f_id, name, cat_name, cal, p, f, c, portion in foods:
                    list_container.add_widget(TwoLineListItem(
                        text=f"   {name}", secondary_text=f"   {cal} ккал | Б:{p} Ж:{f} У:{c} (Порция: {portion}г)",
                        on_release=lambda x, fn=name, fc=cal, fp=p, ff=f, fcarbs=c: self.add_selected_food(fn, fc, fp, ff, fcarbs)
                    ))

    def toggle_category(self, category):
        if category in self.expanded_categories: self.expanded_categories.remove(category)
        else: self.expanded_categories.add(category)
        self.filter_food_list(self.food_dialog.content_cls.ids.search_field.text)

    def add_selected_food(self, name, calories, protein, fat, carbs):
        database.add_meal(name, calories, protein, fat, carbs)
        self.food_dialog.dismiss()
        self.refresh_dashboard()
        if self.root_widget.ids.sm.current == "main": self.update_meals_ui()

    def change_week(self, delta):
        self.week_offset += delta
        self.render_calendar_days()

    def schedule_setup_calendar(self):
        Clock.schedule_once(lambda dt: self.setup_calendar(), 0.05)

    def setup_calendar(self):
        if not self.selected_workout_date:
            self.selected_workout_date = date.today().isoformat()
        self.render_calendar_days()

    def render_calendar_days(self):
        screen = self.root_widget.ids.sm.get_screen("workouts")
        container = screen.ids.days_container
        container.clear_widgets()

        today = date.today()
        base_date = today + timedelta(days=7 * self.week_offset)
        start_of_week = base_date - timedelta(days=base_date.weekday())
        days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        
        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            date_str = current_date.isoformat()
            
            bg_color = "(0.4, 0.8, 0.6, 1.0)" if date_str == self.selected_workout_date else "((0.2, 0.2, 0.2, 1) if app.theme_cls.theme_style == 'Dark' else (1, 1, 1, 1))"
            
            card = Builder.load_string(f'''
DayCard:
    date_str: "{date_str}"
    day_name: "{days_ru[current_date.weekday()]}"
    day_num: "{current_date.day}"
    md_bg_color: {bg_color}
''')
            container.add_widget(card)
            
        self.select_workout_date(self.selected_workout_date)

    def select_workout_date(self, date_str):
        if self.selected_workout_date:
            self.save_workout_plan()

        self.selected_workout_date = date_str
        screen = self.root_widget.ids.sm.get_screen("workouts")
        
        container = screen.ids.days_container
        for child in container.children:
            if child.date_str == date_str:
                child.md_bg_color = [0.4, 0.8, 0.6, 1.0]
                child.children[0].text_color = [1, 1, 1, 1] 
                child.children[1].text_color = [1, 1, 1, 1] 
            else:
                child.md_bg_color = [0.2, 0.2, 0.2, 1] if self.theme_cls.theme_style == "Dark" else [1, 1, 1, 1]
                child.children[0].text_color = [0.8, 0.8, 0.8, 1] if self.theme_cls.theme_style == "Dark" else [0.4, 0.4, 0.4, 1]
                child.children[1].text_color = [1, 1, 1, 1] if self.theme_cls.theme_style == "Dark" else [0.1, 0.1, 0.1, 1]
        
        screen.ids.selected_date_label.text = f"План на {date_str}"
        screen.ids.workout_note.text = database.get_workout_plan(date_str)

    def save_workout_plan(self):
        if not self.selected_workout_date: return
        screen = self.root_widget.ids.sm.get_screen("workouts")
        database.save_workout_plan(self.selected_workout_date, screen.ids.workout_note.text)

    def show_goals_dialog(self):
        if not self.goals_dialog:
            self.goals_dialog = MDDialog(
                title="Моя суточная норма", type="custom", content_cls=GoalsDataContent(),
                buttons=[
                    MDFlatButton(text="ОТМЕНА", theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), on_release=lambda x: self.goals_dialog.dismiss()),
                    MDFlatButton(text="СОХРАНИТЬ", theme_text_color="Custom", text_color=(1, 0.6, 0.2, 1), on_release=self.save_goals),
                ],
            )
        goals = database.get_daily_goals()
        self.goals_dialog.content_cls.ids.cal_field.text = str(goals[0])
        self.goals_dialog.content_cls.ids.p_field.text = str(goals[1])
        self.goals_dialog.content_cls.ids.f_field.text = str(goals[2])
        self.goals_dialog.content_cls.ids.c_field.text = str(goals[3])
        self.goals_dialog.open()

    def save_goals(self, *args):
        cls = self.goals_dialog.content_cls.ids
        cal = int(cls.cal_field.text) if cls.cal_field.text.isdigit() else 2000
        p = int(cls.p_field.text) if cls.p_field.text.isdigit() else 150
        f = int(cls.f_field.text) if cls.f_field.text.isdigit() else 70
        c = int(cls.c_field.text) if cls.c_field.text.isdigit() else 200
        database.update_user_goals(cal, p, f, c)
        self.goals_dialog.dismiss()
        self.refresh_dashboard()

    def show_personal_data_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Ваши данные", type="custom", content_cls=PersonalDataContent(),
                buttons=[
                    MDFlatButton(text="ОТМЕНА", theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), on_release=lambda x: self.dialog.dismiss()),
                    MDFlatButton(text="СОХРАНИТЬ", theme_text_color="Custom", text_color=(0.4, 0.8, 0.6, 1), on_release=self.save_personal_data),
                ],
            )
        self.dialog.content_cls.ids.name_field.text = self.user_data.get("name", "")
        self.dialog.content_cls.ids.age_field.text = self.user_data.get("age", "")
        self.dialog.content_cls.ids.weight_field.text = self.user_data.get("weight", "")
        self.dialog.content_cls.ids.height_field.text = self.user_data.get("height", "")
        if self.user_data.get("gender") == "male": self.dialog.content_cls.ids.check_male.active = True
        else: self.dialog.content_cls.ids.check_female.active = True
        self.dialog.open()

    def save_personal_data(self, *args):
        raw_name = self.dialog.content_cls.ids.name_field.text.strip()
        new_name = raw_name if raw_name else "Пользователь"
        new_age = self.dialog.content_cls.ids.age_field.text
        new_weight = self.dialog.content_cls.ids.weight_field.text
        new_height = self.dialog.content_cls.ids.height_field.text
        new_gender = "male" if self.dialog.content_cls.ids.check_male.active else "female"

        database.save_user_data(new_name, new_age, new_weight, new_height, new_gender)
        self.user_data = {"name": new_name, "age": new_age, "weight": new_weight, "height": new_height, "gender": new_gender}
        self.update_ui_with_user_data()
        self.dialog.dismiss()

    def update_ui_with_user_data(self):
        main_screen = self.root_widget.ids.sm.get_screen("main")
        profile_screen = self.root_widget.ids.sm.get_screen("profile")
        
        name = self.user_data.get("name", "Пользователь")
        main_screen.ids.main_name_label.text = f"Привет, {name.split()[0]}!"
        profile_screen.ids.profile_name_label.text = name

        new_icon = "face-man" if self.user_data.get("gender") == "male" else "face-woman"
        main_screen.ids.main_avatar.icon = new_icon
        profile_screen.ids.profile_avatar.icon = new_icon

if __name__ == "__main__":
    CalCoreApp().run()
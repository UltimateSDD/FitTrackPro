# main.py
import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup
from kivy.utils import platform
import os
import json
import requests
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.camera import Camera
from kivy.uix.gridlayout import GridLayout


# Конфигурация
Window.size = (360, 640)

# --- Путь к хранилищу данных ---
if platform == 'android':
    storage_path = '/sdcard/fittrackpro'
else:
    storage_path = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(storage_path):
    os.makedirs(storage_path)

store = JsonStore(os.path.join(storage_path, 'fittrackpro_data.json'))


# --- Вспомогательные функции ---
def save_data(key, value):
    store.put(key, value=value)


def load_data(key):
    if store.exists(key):
        return store.get(key)['value']
    else:
        return None


# --- Классы экранов ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Greetings Label
        self.greeting_label = Label(text='Привет!', font_size=32, halign='center', size_hint_y=None, height=60)
        layout.add_widget(self.greeting_label)


        # Buttons Grid
        buttons_grid = GridLayout(cols=2, size_hint_y=None, height=150, spacing=10)  # Reduced height
        workout_button = Button(text='Тренировки', on_press=lambda x: self.switch_to_screen('workout'))
        nutrition_button = Button(text='Питание', on_press=lambda x: self.switch_to_screen('nutrition'))
        profile_button = Button(text='Профиль', on_press=lambda x: self.switch_to_screen('profile'))
        buttons_grid.add_widget(workout_button)
        buttons_grid.add_widget(nutrition_button)
        buttons_grid.add_widget(profile_button)
        layout.add_widget(buttons_grid)

        self.add_widget(layout)

    def load_data(self):
        # Load User Name
        profile_data = load_data('profile')
        if profile_data and 'name' in profile_data:
            name = profile_data['name']
            self.greeting_label.text = f'Привет, {name}!'
        else:
            self.greeting_label.text = 'Привет!'

    def switch_to_screen(self, screen_name):
        self.manager.current = screen_name


class WorkoutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        title_label = Label(text='Тренировки', font_size=24, halign='center', size_hint_y=None, height=40)
        layout.add_widget(title_label)

        # Добавление тренировки
        add_workout_button = Button(text='Добавить тренировку', size_hint_y=None, height=40)
        add_workout_button.bind(on_press=lambda x: self.show_add_workout_popup())
        layout.add_widget(add_workout_button)

        # Список тренировок
        self.workout_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.workout_list.bind(minimum_height=self.workout_list.setter('height'))

        scroll_view = ScrollView()
        scroll_view.add_widget(self.workout_list)
        layout.add_widget(scroll_view)

        back_button = Button(text='Назад', size_hint_y=None, height=40)
        back_button.bind(on_press=lambda x: self.switch_to_screen('main'))
        layout.add_widget(back_button)

        self.add_widget(layout)
        self.workouts = []  # Initialize workouts list
        self.load_workouts()

    def switch_to_screen(self, screen_name):
        self.manager.current = screen_name

    def show_add_workout_popup(self):
        popup = AddWorkoutPopup(self)
        popup.open()

    def add_workout(self, workout_data):
        self.workouts.append(workout_data)
        self.update_workout_list()
        self.save_workouts()

    def update_workout_list(self):
        self.workout_list.clear_widgets()
        for i, workout in enumerate(self.workouts):
            workout_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
            workout_label = Label(text=f"{workout['name']} ({workout['duration']} мин)", size_hint_x=0.7)
            workout_layout.add_widget(workout_label)

            delete_button = Button(text='Удалить', size_hint_x=0.3)
            delete_button.bind(on_press=lambda instance, index=i: self.delete_workout(index))  # Pass index to delete_workout
            workout_layout.add_widget(delete_button)

            self.workout_list.add_widget(workout_layout)

    def delete_workout(self, index):
        del self.workouts[index]
        self.update_workout_list()
        self.save_workouts()

    def save_workouts(self):
        workout_data = [workout for workout in self.workouts]  # Convert workouts to a list
        save_data('workouts', workout_data)

    def load_workouts(self):
        loaded_workouts = load_data('workouts')
        if loaded_workouts:
            self.workouts = loaded_workouts
        else:
            self.workouts = []
        self.update_workout_list()

class NutritionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.food_items = []
        self.recipes = []  # To store recipes
        self.selected_recipe = None
        self.setup_ui()
        self.load_food_items()
        self.load_recipes()

    def setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        title_label = Label(text='Питание', font_size=24, halign='center', size_hint_y=None, height=40)
        layout.add_widget(title_label)

        # Add Food Button
        add_food_button = Button(text='Добавить продукт', size_hint_y=None, height=40)
        add_food_button.bind(on_press=self.show_add_food_popup)
        layout.add_widget(add_food_button)

        # Add Recipe Button
        add_recipe_button = Button(text='Добавить рецепт', size_hint_y=None, height=40)
        add_recipe_button.bind(on_press=self.show_add_recipe_popup)
        layout.add_widget(add_recipe_button)

        # Recipes List
        recipe_label = Label(text='Рецепты:', size_hint_y=None, height=30)
        layout.add_widget(recipe_label)

        self.recipe_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.recipe_list.bind(minimum_height=self.recipe_list.setter('height'))
        recipe_scroll_view = ScrollView()
        recipe_scroll_view.add_widget(self.recipe_list)
        layout.add_widget(recipe_scroll_view)

        # Selected Recipe Details
        self.selected_recipe_label = Label(text='Детали рецепта:', size_hint_y=None, height=30)
        layout.add_widget(self.selected_recipe_label)

        self.recipe_details = Label(text='', halign='left', valign='top', size_hint_y=None,
                                     text_size=(self.width - 20, None))
        self.recipe_details.bind(texture_size=lambda *args: self.recipe_details.setter('height')(self.recipe_details,
                                                                                                  self.recipe_details.texture_size[
                                                                                                      1] + 20))  # update height based on texture size
        recipe_details_scroll_view = ScrollView()
        recipe_details_scroll_view.add_widget(self.recipe_details)
        layout.add_widget(recipe_details_scroll_view)

        # Food List
        food_label = Label(text='Продукты:', size_hint_y=None, height=30)
        layout.add_widget(food_label)

        self.food_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.food_list.bind(minimum_height=self.food_list.setter('height'))
        scroll_view = ScrollView()
        scroll_view.add_widget(self.food_list)
        layout.add_widget(scroll_view)

        # Nutrition Info Label
        self.nutrition_info_label = Label(text='Информация о питании: ', size_hint_y=None, height=30)
        layout.add_widget(self.nutrition_info_label)

        # Buttons
        buttons_layout = BoxLayout(size_hint_y=None, height=40, spacing=10,
                                   padding=[10, 10, 10, 10])  # left, top, right, bottom
        back_button = Button(text='Назад', size_hint=(0.2, 1),
                             on_press=lambda x: self.switch_to_screen('main'))  # Adjust size_hint for button width
        buttons_layout.add_widget(back_button)
        layout.add_widget(buttons_layout)

        self.add_widget(layout)

        self.update_recipe_list()  # Load Recipes on start

    def switch_to_screen(self, screen_name):
        self.manager.current = screen_name

    # --- Food Management ---
    def show_add_food_popup(self, instance):
        popup = AddFoodPopup(self)
        popup.open()

    def add_food_item(self, food_data):
        self.food_items.append(food_data)
        self.update_food_list()
        self.save_food_items()
        self.update_nutrition_info()

    def update_food_list(self):
        self.food_list.clear_widgets()
        for i, food in enumerate(self.food_items):
            food_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
            food_label = Label(text=f"{food['name']} ({food['quantity']} {food['unit']})", size_hint_x=0.7)
            food_layout.add_widget(food_label)
            delete_button = Button(text='Удалить', size_hint_x=0.3)
            delete_button.bind(on_press=lambda instance, index=i: self.delete_food_item(index))
            food_layout.add_widget(delete_button)
            self.food_list.add_widget(food_layout)

    def delete_food_item(self, index):
        del self.food_items[index]
        self.update_food_list()
        self.save_food_items()
        self.update_nutrition_info()

    def save_food_items(self):
        food_data = [food for food in self.food_items]
        save_data('food_items', food_data)

    def load_food_items(self):
        loaded_food_items = load_data('food_items')
        if loaded_food_items:
            self.food_items = loaded_food_items
        else:
            self.food_items = []
        self.update_food_list()
        self.update_nutrition_info()

    # --- Recipe Management ---
    def show_add_recipe_popup(self, instance):
        popup = AddRecipePopup(self, recipe=None)  # Pass None for new recipe
        popup.open()

    def add_recipe(self, recipe_data):
        if self.selected_recipe:
            # Edit existing recipe
            index = self.recipes.index(self.selected_recipe)
            self.recipes[index] = recipe_data
            self.selected_recipe = None
        else:
            # Add new recipe
            self.recipes.append(recipe_data)
        self.save_recipes()
        self.update_recipe_list()

    def delete_recipe(self, recipe):
        self.recipes.remove(recipe)
        self.save_recipes()
        self.update_recipe_list()
        self.recipe_details.text = ''

    def save_recipes(self):
        recipes_data = [recipe for recipe in self.recipes]
        save_data('recipes', recipes_data)

    def load_recipes(self):
        loaded_recipes = load_data('recipes')
        if loaded_recipes:
            self.recipes = loaded_recipes
            self.update_recipe_list()
        else:
            self.recipes = []

    def update_recipe_list(self):
        self.recipe_list.clear_widgets()
        for i, recipe in enumerate(self.recipes):
            recipe_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)  # Задайте высоту явно

            recipe_button = Button(text=recipe['name'], size_hint_x=0.6, halign='left')
            recipe_button.bind(on_press=lambda instance, recipe=recipe: self.show_recipe_details(recipe))
            recipe_layout.add_widget(recipe_button)

            edit_button = Button(text='Редактировать', size_hint_x=0.2)
            edit_button.bind(on_press=lambda instance, recipe=recipe: self.show_edit_recipe_popup(recipe))
            recipe_layout.add_widget(edit_button)

            delete_button = Button(text='Удалить', size_hint_x=0.2)
            delete_button.bind(on_press=lambda instance, recipe=recipe: self.delete_recipe(recipe))
            recipe_layout.add_widget(delete_button)

            self.recipe_list.add_widget(recipe_layout)

    def show_recipe_details(self, recipe):
        self.selected_recipe = recipe
        ingredients_text = '\n'.join(recipe['ingredients'])
        instructions_text = recipe['instructions']

        recipe_text = (
            f"**Ингредиенты:**\n{ingredients_text}\n\n"
            f"**Инструкции:**\n{instructions_text}"
        )
        self.recipe_details.text = recipe_text

    def show_edit_recipe_popup(self, recipe):
        self.selected_recipe = recipe
        popup = AddRecipePopup(self, recipe=recipe)  # Pass recipe data
        popup.open()

    # --- Nutrition Calculation ---
    def update_nutrition_info(self):
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0

        # Placeholder Nutrition Data (Replace with actual database or API)
        nutrition_data = {
            'Яблоко': {'calories': 95, 'protein': 0.3, 'carbs': 25, 'fat': 0.3},
            'Банан': {'calories': 105, 'protein': 1.3, 'carbs': 27, 'fat': 0.4},
            'Курица (100г)': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6}
        }

        for food in self.food_items:
            name = food['name']
            quantity = food['quantity']
            if name in nutrition_data:
                calories = nutrition_data[name]['calories'] * quantity / 100
                protein = nutrition_data[name]['protein'] * quantity / 100
                carbs = nutrition_data[name]['carbs'] * quantity / 100
                fat = nutrition_data[name]['fat'] * quantity / 100

                total_calories += calories
                total_protein += protein
                total_carbs += carbs
                total_fat += fat

        self.nutrition_info_label.text = (
            f'Калории: {total_calories:.2f}\n'
            f'Белки: {total_protein:.2f} г\n'
            f'Углеводы: {total_carbs:.2f} г\n'
            f'Жиры: {total_fat:.2f} г'
        )

# --- Popups ---
class AddFoodPopup(Popup):
    # (Код AddFoodPopup остается без изменений)
    pass

# --- Popups ---
class AddFoodPopup(Popup):
    def __init__(self, nutrition_screen, **kwargs):
        super().__init__(**kwargs)
        self.nutrition_screen = nutrition_screen
        self.title = 'Добавить продукт'
        self.size_hint = (None, None)
        self.size = (300, 350)

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Name Input
        self.name_input = TextInput(hint_text='Название продукта', size_hint_y=None, height=30)
        content.add_widget(self.name_input)

        # Quantity Input
        self.quantity_input = TextInput(hint_text='Количество', input_type='number', size_hint_y=None, height=30)
        content.add_widget(self.quantity_input)

        # Unit Input
        self.unit_input = TextInput(hint_text='Единица измерения (г, мл, шт.)', size_hint_y=None, height=30)
        content.add_widget(self.unit_input)

        # Barcode Scan Button
        scan_barcode_button = Button(text='Сканировать штрих-код', size_hint_y=None, height=40)
        scan_barcode_button.bind(on_press=self.show_barcode_scanner)
        content.add_widget(scan_barcode_button)

        # Buttons Layout
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        cancel_button = Button(text='Отмена')
        cancel_button.bind(on_press=self.dismiss)
        buttons_layout.add_widget(cancel_button)
        add_button = Button(text='Добавить')
        add_button.bind(on_press=self.add_food)
        buttons_layout.add_widget(add_button)
        content.add_widget(buttons_layout)

        self.content = content

    def add_food(self, instance):
        name = self.name_input.text
        quantity = self.quantity_input.text
        unit = self.unit_input.text
        try:
            quantity = float(quantity)
            if name and quantity > 0 and unit:
                food_data = {'name': name, 'quantity': quantity, 'unit': unit}
                self.nutrition_screen.add_food_item(food_data)
                self.dismiss()
            else:
                print('Пожалуйста, заполните все поля корректно.')
        except ValueError:
            print('Количество должно быть числом.')

    def show_barcode_scanner(self, instance):
        # Placeholder for barcode scanner integration
        print("Функция сканирования штрих-кода пока не реализована.")


class AddRecipePopup(Popup):
    def __init__(self, nutrition_screen, recipe=None, **kwargs):
        super().__init__(**kwargs)
        self.nutrition_screen = nutrition_screen
        self.title = 'Добавить рецепт'
        self.size_hint = (None, None)
        self.size = (400, 400)

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Name Input
        self.name_input = TextInput(hint_text='Название рецепта', size_hint_y=None, height=30)
        content.add_widget(self.name_input)

        # Ingredients Input (Multi-line)
        self.ingredients_input = TextInput(hint_text='Ингредиенты (каждый с новой строки)', multiline=True, size_hint_y=0.5)
        content.add_widget(self.ingredients_input)

        # Instructions Input (Multi-line)
        self.instructions_input = TextInput(hint_text='Инструкции', multiline=True, size_hint_y=0.5)
        content.add_widget(self.instructions_input)

        # Buttons Layout
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        cancel_button = Button(text='Отмена')
        cancel_button.bind(on_press=self.dismiss)
        buttons_layout.add_widget(cancel_button)
        add_button = Button(text='Добавить')
        add_button.bind(on_press=self.add_recipe)
        buttons_layout.add_widget(add_button)
        content.add_widget(buttons_layout)

        self.content = content

        # Load recipe data if editing
        if recipe:
            self.name_input.text = recipe['name']
            self.ingredients_input.text = '\n'.join(recipe['ingredients'])
            self.instructions_input.text = recipe['instructions']

    def add_recipe(self, instance):
        name = self.name_input.text
        ingredients = self.ingredients_input.text.split('\n')
        instructions = self.instructions_input.text

        if name and ingredients and instructions:
            recipe_data = {
                'name': name,
                'ingredients': ingredients,
                'instructions': instructions
            }
            self.nutrition_screen.add_recipe(recipe_data)
            self.dismiss()
        else:
            print('Пожалуйста, заполните все поля рецепта.')

# --- Helper Functions and Classes ---
# Placeholder for Barcode Scanning
class BarcodeScannerPopup(Popup):
    # (Код BarcodeScannerPopup остается без изменений)
    pass

# Replace this with your actual food database or API integration
def get_food_data_from_barcode(barcode):
    # This is a dummy function that always returns the same apple data
    # A real function would use the barcode to query a database or API
    if barcode == '123456789':
        return {'name': 'Яблоко', 'calories': 95, 'protein': 0.3, 'carbs': 25, 'fat': 0.3}
    else:
        return None

# Пример использования JsonStore (убедитесь, что он правильно настроен в main.py)
def save_data(key, value):
    store.put(key, value=value)

def load_data(key):
    if store.exists(key):
        return store.get(key)['value']
    else:
        return None

# --- Helper Functions and Classes ---
# Placeholder for Barcode Scanning
class BarcodeScannerPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Сканировать штрих-код'
        self.size_hint = (None, None)
        self.size = (400, 400)
        # Camera integration logic would go here in a real application
        self.content = Label(text='Камера и сканирование штрих-кода не реализованы.')

# Replace this with your actual food database or API integration
def get_food_data_from_barcode(barcode):
    # This is a dummy function that always returns the same apple data
    # A real function would use the barcode to query a database or API
    if barcode == '123456789':
        return {'name': 'Яблоко', 'calories': 95, 'protein': 0.3, 'carbs': 25, 'fat': 0.3}
    else:
        return None

# Пример использования JsonStore (убедитесь, что он правильно настроен в main.py)
def save_data(key, value):
    store.put(key, value=value)

def load_data(key):
    if store.exists(key):
        return store.get(key)['value']
    else:
        return None

class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        title_label = Label(text='Профиль', font_size=24, halign='center', size_hint_y=None, height=40)
        layout.add_widget(title_label)

        # Поля для ввода данных
        self.name_input = TextInput(hint_text='Имя', size_hint_y=None, height=30)
        layout.add_widget(self.name_input)

        self.age_input = TextInput(hint_text='Возраст', input_type='number', size_hint_y=None, height=30)
        layout.add_widget(self.age_input)

        self.height_input = TextInput(hint_text='Рост (см)', input_type='number', size_hint_y=None, height=30)
        layout.add_widget(self.height_input)

        self.weight_input = TextInput(hint_text='Вес (кг)', input_type='number', size_hint_y=None, height=30)
        layout.add_widget(self.weight_input)

        # Кнопка сохранения
        save_button = Button(text='Сохранить', size_hint_y=None, height=40)
        save_button.bind(on_press=self.save_profile)
        layout.add_widget(save_button)

        # Вывод сохраненных данных (лейблы)
        self.name_label = Label(text='Имя: ', size_hint_y=None, height=30)
        layout.add_widget(self.name_label)

        self.age_label = Label(text='Возраст: ', size_hint_y=None, height=30)
        layout.add_widget(self.age_label)

        self.height_label = Label(text='Рост: ', size_hint_y=None, height=30)
        layout.add_widget(self.height_label)

        self.weight_label = Label(text='Вес: ', size_hint_y=None, height=30)
        layout.add_widget(self.weight_label)

        back_button = Button(text='Назад', size_hint_y=None, height=40)
        back_button.bind(on_press=lambda x: self.switch_to_screen('main'))
        layout.add_widget(back_button)

        self.add_widget(layout)
        self.load_profile()

    def switch_to_screen(self, screen_name):
        self.manager.current = screen_name

    def save_profile(self, instance):
        name = self.name_input.text
        age = self.age_input.text
        height = self.height_input.text
        weight = self.weight_input.text

        try:
            age = int(age)
            height = float(height)
            weight = float(weight)

            if name and age > 0 and height > 0 and weight > 0:
                profile_data = {'name': name, 'age': age, 'height': height, 'weight': weight}
                save_data('profile', profile_data)
                self.update_profile_labels(profile_data)  # Обновляем лейблы
                print('Профиль сохранен')
            else:
                print('Пожалуйста, заполните все поля корректно.')

        except ValueError:
            print('Возраст, рост и вес должны быть числами.')

    def load_profile(self):
        loaded_profile = load_data('profile')
        if loaded_profile:
            self.name_input.text = loaded_profile['name']
            self.age_input.text = str(loaded_profile['age'])
            self.height_input.text = str(loaded_profile['height'])
            self.weight_input.text = str(loaded_profile['weight'])
            self.update_profile_labels(loaded_profile)  # Обновляем лейблы
        else:
            print('Профиль не найден')

    def update_profile_labels(self, profile_data):
        self.name_label.text = f"Имя: {profile_data['name']}"
        self.age_label.text = f"Возраст: {profile_data['age']}"
        self.height_label.text = f"Рост: {profile_data['height']} см"
        self.weight_label.text = f"Вес: {profile_data['weight']} кг"


# --- Всплывающее окно для добавления тренировки ---
class AddWorkoutPopup(Popup):
    def __init__(self, workout_screen, **kwargs):
        super().__init__(**kwargs)
        self.workout_screen = workout_screen
        self.title = 'Добавить тренировку'
        self.size_hint = (None, None)
        self.size = (300, 250)

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.name_input = TextInput(hint_text='Название тренировки', size_hint_y=None, height=30)
        content.add_widget(self.name_input)

        self.duration_input = TextInput(hint_text='Длительность (мин)', input_type='number', size_hint_y=None,
                                        height=30)
        content.add_widget(self.duration_input)

        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        cancel_button = Button(text='Отмена')
        cancel_button.bind(on_press=self.dismiss)
        buttons_layout.add_widget(cancel_button)

        add_button = Button(text='Добавить')
        add_button.bind(on_press=self.add_workout)
        buttons_layout.add_widget(add_button)

        content.add_widget(buttons_layout)

        self.content = content

    def add_workout(self, instance):
        name = self.name_input.text
        duration = self.duration_input.text
        try:
            duration = int(duration)
            if name and duration > 0:
                workout_data = {'name': name, 'duration': duration}
                self.workout_screen.add_workout(workout_data)
                self.dismiss()
            else:
                print('Пожалуйста, введите название и корректную длительность.')
        except ValueError:
            print('Длительность должна быть числом.')


# --- Screen Manager ---
class FitTrackApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(WorkoutScreen(name='workout'))
        sm.add_widget(NutritionScreen(name='nutrition'))
        sm.add_widget(ProfileScreen(name='profile'))
        return sm


if __name__ == '__main__':
    FitTrackApp().run()

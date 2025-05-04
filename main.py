import os
from dotenv import load_dotenv
from telebot import types
import requests
from urllib.parse import quote
import folium
from folium.plugins import AntPath
import telebot

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

PAGE_SIZE = 5
user_data = {}

def get_categories():
    return ["Здания", "Памятники", "Личности", "Традиции"]

def get_objects_by_category(category):
    objects = {
        "Здания": [
            {"name": "Кремль", "lat": 55.7517, "lon": 37.6178},
            {"name": "Храм Василия Блаженного", "lat": 55.7525, "lon": 37.6231},
            {"name": "Большой театр", "lat": 55.7601, "lon": 37.6186},
            {"name": "ГУМ", "lat": 55.7547, "lon": 37.6217},
            {"name": "МГУ", "lat": 55.7039, "lon": 37.5287}
        ],
        "Памятники": [
            {"name": "Царь-пушка", "lat": 55.7507, "lon": 37.6179},
            {"name": "Памятник Пушкину", "lat": 55.7646, "lon": 37.6066},
            {"name": "Монумент Победы", "lat": 55.7303, "lon": 37.5048},
            {"name": "Памятник Минину и Пожарскому", "lat": 55.7525, "lon": 37.6231},
            {"name": "Памятник Гагарину", "lat": 55.7103, "lon": 37.5857}
        ],
        "Личности": {
            "Ректоры и профессора": ["Петр I", "Лев Толстой", "Александр Пушкин", "Анна Ахматова", "Максим Горький"],
            "Выпускники": ["Иван Иванов", "Дмитрий Дмитриев", "Анна Васильева", "Петр Петров", "Сергей Сергеев"],
            "Учёные": ["Эйнштейн", "Ньютон", "Пуанкаре", "Коперник", "Гагарин"],
            "Конструкторы": ["Королев", "Циолковский", "Туполев", "Микоян", "Яковлев"],
            "Общественные деятели": ["Ленин", "Троцкий", "Мартин Лютер Кинг", "Ганди", "Нельсон Мандела"],
            "Нобелевские лауреаты": ["Пастер", "Менделеев", "Флеминг", "Шульц", "Тимоти Хант"]
        },
        "Традиции": ["Масленица", "Пасха", "Новый год", "День Победы", "Рождество"]
    }
    return objects.get(category, {})

def generate_markup(page=0, category=None, subcategory=None):
    markup = types.InlineKeyboardMarkup()
    
    if category == "Личности" and subcategory:
        full_list = get_objects_by_category(category).get(subcategory, [])
    else:
        full_list = get_objects_by_category(category)

    total_pages = (len(full_list) + PAGE_SIZE - 1) // PAGE_SIZE
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    
    for item in full_list[start:end]:
        if isinstance(item, dict):
            button_text = item['name']
            callback_data = f"item_{item['name']}"
        else:
            button_text = item
            callback_data = f"item_{item}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    control_buttons = []
    prev_data = f"page|{page-1}|{category}|{subcategory if subcategory else 'None'}"
    next_data = f"page|{page+1}|{category}|{subcategory if subcategory else 'None'}"
    
    if page > 0:
        control_buttons.append(types.InlineKeyboardButton("← Назад", callback_data=prev_data))
    if end < len(full_list):
        control_buttons.append(types.InlineKeyboardButton("Вперед →", callback_data=next_data))
    
    if control_buttons:
        markup.row(*control_buttons)
    
    markup.row(types.InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    return markup, total_pages

@bot.message_handler(commands=['start'])
def send_welcome(message):
    show_category_menu(message.chat.id)

def show_category_menu(chat_id):
    text = "Привет! Я бот-гид. Выберите категорию:"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*[types.KeyboardButton(category) for category in get_categories()])
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text not in get_categories() and m.text != '/start')
def handle_unknown(message):
    bot.send_message(message.chat.id, "Пожалуйста, выберите категорию из меню ниже или напишите /start.")

@bot.message_handler(func=lambda m: m.text in get_categories())
def handle_category_selection(message):
    chat_id = message.chat.id
    category = message.text
    user_data[chat_id] = {'category': category}
    
    bot.send_message(chat_id, "Используйте кнопки ниже для навигации:", reply_markup=types.ReplyKeyboardRemove())
    
    if category == "Личности":
        show_subcategory_menu(chat_id)
    else:
        markup, total_pages = generate_markup(0, category)
        msg = bot.send_message(chat_id, f"Страница 1 из {total_pages}", reply_markup=markup)
        user_data[chat_id]['page'] = 0
        user_data[chat_id]['message_id'] = msg.message_id

def show_subcategory_menu(chat_id):
    text = "Выберите подкатегорию:"
    subcategories = list(get_objects_by_category("Личности").keys())
    markup = types.InlineKeyboardMarkup()
    for subcat in subcategories:
        markup.add(types.InlineKeyboardButton(subcat, callback_data=f"subcat_{subcat}"))
    markup.add(types.InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('subcat_'))
def handle_subcategory_selection(call):
    chat_id = call.message.chat.id
    subcategory = call.data.split('_')[1]
    category = "Личности"
    user_data[chat_id]['subcategory'] = subcategory
    
    markup, total_pages = generate_markup(0, category, subcategory)
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Страница 1 из {total_pages}",
        reply_markup=markup
    )
    user_data[chat_id]['page'] = 0
    user_data[chat_id]['message_id'] = call.message.message_id
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('page|'))
def handle_page_navigation(call):
    chat_id = call.message.chat.id
    data = call.data.split('|')
    page = int(data[1])
    category = data[2]
    subcategory = data[3] if data[3] != 'None' else None
    
    markup, total_pages = generate_markup(page, category, subcategory)
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Страница {page+1} из {total_pages}",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def handle_main_menu(call):
    chat_id = call.message.chat.id
    bot.delete_message(chat_id, call.message.message_id)
    show_category_menu(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('item_'))
@bot.callback_query_handler(func=lambda call: call.data.startswith('item_'))
def handle_item_selection(call):
    chat_id = call.message.chat.id
    item_name = call.data.split('_', 1)[1]
    bot.answer_callback_query(call.id)
    
    user_info = user_data.get(chat_id, {})
    category = user_info.get('category', '')
    subcategory = user_info.get('subcategory', None)
    
    objects = get_objects_by_category(category)
    if subcategory:
        objects = objects.get(subcategory, [])
    
    selected_obj = None
    for obj in objects:
        if isinstance(obj, dict) and obj['name'] == item_name:
            selected_obj = obj
            break
        elif isinstance(obj, str) and obj == item_name:
            selected_obj = {'name': item_name}
    
    if selected_obj:
        user_data[chat_id]['selected_object'] = selected_obj
    
    response = f"Информация о {item_name}."
    markup = types.InlineKeyboardMarkup()
    
    if category in ["Здания", "Памятники"] and isinstance(selected_obj, dict) and 'lat' in selected_obj and 'lon' in selected_obj:
        markup.add(types.InlineKeyboardButton("Построить маршрут", callback_data="request_route"))
    
    bot.send_message(chat_id, response, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'request_route')
def handle_route_request(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Пожалуйста, отправьте вашу геолокацию для построения маршрута.")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    chat_id = message.chat.id
    try:
        user_lat = message.location.latitude
        user_lon = message.location.longitude
        
        if 'selected_object' not in user_data.get(chat_id, {}):
            bot.send_message(chat_id, "❌ Сначала выберите объект из меню!")
            return
            
        obj = user_data[chat_id]['selected_object']
        if 'lat' not in obj or 'lon' not in obj:
            bot.send_message(chat_id, "❌ У объекта нет координат!")
            return

        url = f"http://router.project-osrm.org/route/v1/driving/{user_lon},{user_lat};{obj['lon']},{obj['lat']}?overview=full&geometries=geojson"
        response = requests.get(url)
        data = response.json()

        if data['code'] != 'Ok':
            raise Exception("OSRM routing error")

        route = data['routes'][0]
        distance = route['distance']/1000  # в километрах
        duration = route['duration']/60    # в минутах
        coordinates = [(lat, lon) for lon, lat in route['geometry']['coordinates']]

        m = folium.Map(
            location=[(user_lat + obj['lat'])/2, (user_lon + obj['lon'])/2],
            zoom_start=13,
            tiles="CartoDB positron"
        )

        folium.Marker(
            [user_lat, user_lon],
            popup="Ваше местоположение",
            icon=folium.Icon(color="green", icon="user")
        ).add_to(m)

        folium.Marker(
            [obj['lat'], obj['lon']],
            popup=obj['name'],
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)

        AntPath(
            locations=coordinates,
            color='#1E90FF',
            weight=6,
            dash_array=[10, 20]
        ).add_to(m)

        folium.map.Marker(
            [user_lat, user_lon],
            icon=folium.DivIcon(
                icon_size=(250, 36),
                icon_anchor=(0, 0),
                html=f'<div style="font-size: 14px; background: white; padding: 5px; border-radius: 5px;">'
                     f'<b>Дистанция:</b> {distance:.1f} км<br>'
                     f'<b>Время:</b> {duration:.1f} мин</div>'
            )
        ).add_to(m)

        filename = f"route_{chat_id}.html"
        m.save(filename)
        
        with open(filename, 'rb') as f:
            bot.send_document(
                chat_id,
                f,
                caption=f"Маршрут к {obj['name']}",
                parse_mode="HTML"
            )
        
        os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Ошибка построения маршрута: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
import os
from dotenv import load_dotenv
from telebot import types
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
        "Здания": ["Кремль", "Храм Василия Блаженного", "Большой театр", "ГУМ", "МГУ"],
        "Памятники": ["Царь-пушка", "Памятник Пушкину", "Монумент Победы", "Памятник Минину и Пожарскому", "Памятник Гагарину"],
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
        markup.add(types.InlineKeyboardButton(item, callback_data=f"item_{item}"))
    
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
    
    # Удаляем reply-клавиатуру
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
def handle_item_selection(call):
    chat_id = call.message.chat.id
    item_name = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    
    category = user_data.get(chat_id, {}).get('category', '')
    response = f"Информация о {item_name}."
    markup = types.InlineKeyboardMarkup()
    
    if category in ["Здания", "Памятники"]:
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
    user_info = user_data.get(chat_id, {})
    if user_info.get('category') in ["Здания", "Памятники"]:
        bot.send_message(chat_id, "Маршрут построен!")
    else:
        bot.send_message(chat_id, "Для выбранной категории маршруты не доступны.")

if __name__ == "__main__":
    bot.infinity_polling()
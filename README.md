# Polytech Guide Bot - Телеграм-бот для изучения истории университета / University History Telegram Bot

## Описание / Description 
**Polytech Guide Bot** - это интерактивный телеграм-бот, который помогает пользователям изучать исторические объекты, личности и традиции университета. Бот предоставляет информацию о зданиях, памятниках, выдающихся личностях и традициях, а также может построить маршрут к выбранному объекту. 

**HistoryGuideBot** is an interactive Telegram bot that helps users explore historical objects, personalities and traditions of the university. The bot provides information about buildings, monuments, notable figures and traditions, and can also build a route to the selected object.

## Особенности / Features
- Интерактивное меню с категориями / Interactive menu with categories  
- Информация о зданиях и памятниках / Information about buildings and monuments  
- Биографии выдающихся личностей / Biographies of notable figures  
- Описание традиций / Description of traditions  
- Построение маршрутов / Route building  
- Постраничная навигация / Paginated navigation  
- Интеграция с OSRM / OSRM integration  

## Технологии / Technologies  
- Python 3  
- python-telegram-bot  
- Folium (для карт / for maps)  
- OSRM API (для маршрутов / for routing)  
- MySQL (база данных / database)  
- dotenv (для конфигурации / for configuration)  

## Установка / Installation  
1. Клонировать репозиторий / Clone repository:  
  `git clone https://github.com/yourusername/HistoryGuideBot.git`  
  `cd HistoryGuideBot`  
2. Создать .env файл / Create .env file:  
  ```
  BOT_TOKEN=your_telegram_bot_token
  DB_HOST=your_database_host
  DB_USER=your_database_user
  DB_PASSWORD=your_database_password
  DB_NAME=your_database_name
  ```
3. Запустить бота / Run the bot:  
  `python main.py`  

## База данных / Database  
Таблицы / Tables:  
- Building (здания)  
- Sight (памятники)  
- Category (категории)  
- Person (личности)  
- Person_Category (связи)  
- Tradition (традиции)  

## Использование / Usage  
1. Главное меню / Main menu: `/start`  
2. Выбор категории / Select category: `Здания/Buildings`  
3. Построение маршрута / Build route:  
   - Выбрать объект / Select object  
   - Нажать "Построить маршрут" / Click "Build route"  
   - Отправить геолокацию / Send location 

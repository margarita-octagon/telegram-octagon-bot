import telebot
from telebot import types
import os
import requests
import json
import time
from datetime import datetime
import telebot.apihelper

# Получаем переменные из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(BOT_TOKEN)

# Данные пользователей
user_data = {}

# Списки для выбора
CONSTRUCTION_TYPES = ["Скроли", "Екрани", "Щити", "Інше"]
TEAMS = ["Бригада 1", "Бригада 2"]

# Состояния пользователя
STEPS = {
    "OBJECT_CODE": "object_code",
    "CONSTRUCTION_TYPE": "construction_type", 
    "TASK": "task",
    "TEAM": "team",
    "PHOTO_BEFORE": "photo_before",
    "PHOTO_AFTER": "photo_after",
    "COMMENT": "comment"
}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {
        "step": STEPS["OBJECT_CODE"],
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "location": "Київ"  # Всегда Киев по умолчанию
    }
    
    bot.send_message(
        chat_id, 
        "👋 Вітаємо! Давайте оформимо звіт про виконані роботи.\n\n🏢 Введіть код об'єкта:"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    
    # Проверяем, есть ли пользователь в системе
    if chat_id not in user_data:
        bot.send_message(chat_id, "Натисніть /start щоб почати")
        return
    
    current_step = user_data[chat_id]["step"]
    
    # Обработка кода объекта
    if current_step == STEPS["OBJECT_CODE"]:
        user_data[chat_id]["object_code"] = message.text
        user_data[chat_id]["step"] = STEPS["CONSTRUCTION_TYPE"]
        
        # Показываем кнопки с типами конструкций
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for const_type in CONSTRUCTION_TYPES:
            markup.add(types.KeyboardButton(const_type))
        
        bot.send_message(
            chat_id, 
            f"🏢 Код об'єкта: {message.text}\n\n🏗️ Оберіть тип конструкції:",
            reply_markup=markup
        )
    
    # Обработка типа конструкции
    elif current_step == STEPS["CONSTRUCTION_TYPE"]:
        if message.text in CONSTRUCTION_TYPES:
            user_data[chat_id]["construction_type"] = message.text
            user_data[chat_id]["step"] = STEPS["TASK"]
            
            # Убираем клавиатуру
            markup = types.ReplyKeyboardRemove()
            bot.send_message(
                chat_id, 
                f"🏗️ Тип конструкції: {message.text}\n\n📋 Опишіть завдання (що потрібно було зробити):",
                reply_markup=markup
            )
        else:
            bot.send_message(chat_id, "❌ Будь ласка, оберіть тип конструкції зі списку")
    
    # Обработка задания
    elif current_step == STEPS["TASK"]:
        user_data[chat_id]["task"] = message.text
        user_data[chat_id]["step"] = STEPS["TEAM"]
        
        # Показываем кнопки с бригадами
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for team in TEAMS:
            markup.add(types.KeyboardButton(team))
        
        bot.send_message(
            chat_id, 
            f"📋 Завдання: {message.text}\n\n👷 Оберіть виконавця:",
            reply_markup=markup
        )
    
    # Обработка выбора бригады
    elif current_step == STEPS["TEAM"]:
        if message.text in TEAMS:
            user_data[chat_id]["team"] = message.text
            user_data[chat_id]["step"] = STEPS["PHOTO_BEFORE"]
            
            # Кнопка для пропуска фото
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Пропустити"))
            
            bot.send_message(
                chat_id, 
                f"👷 Виконавець: {message.text}\n\n📸 Надішліть фото ДО початку робіт або натисніть 'Пропустити':",
                reply_markup=markup
            )
        else:
            bot.send_message(chat_id, "❌ Будь ласка, оберіть виконавця зі списку")
    
    # Обработка пропуска фото ДО
    elif current_step == STEPS["PHOTO_BEFORE"] and message.text == "Пропустити":
        user_data[chat_id]["photo_before"] = None
        user_data[chat_id]["step"] = STEPS["PHOTO_AFTER"]
        
        # Кнопка для пропуска фото ПОСЛЕ
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Пропустити"))
        
        bot.send_message(
            chat_id, 
            "📸 Тепер надішліть фото ПІСЛЯ виконання робіт або натисніть 'Пропустити':",
            reply_markup=markup
        )
    
    # Обработка пропуска фото ПОСЛЕ
    elif current_step == STEPS["PHOTO_AFTER"] and message.text == "Пропустити":
        user_data[chat_id]["photo_after"] = None
        user_data[chat_id]["step"] = STEPS["COMMENT"]
        
        # Кнопка для пропуска комментария
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Пропустити"))
        
        bot.send_message(
            chat_id, 
            "💬 Додайте коментар або натисніть 'Пропустити':",
            reply_markup=markup
        )
    
    # Обработка комментария
    elif current_step == STEPS["COMMENT"]:
        comment = message.text
        if message.text == "Пропустити":
            comment = "Без коментаря"
        
        user_data[chat_id]["comment"] = comment
        
        # Формируем итоговое сообщение
        photo_before_status = "отримано" if user_data[chat_id].get('photo_before') else "пропущено"
        photo_after_status = "отримано" if user_data[chat_id].get('photo_after') else "пропущено"
        
        summary = f"""
✅ Звіт успішно сформовано!

📅 Дата: {user_data[chat_id]['date']}
📍 Місто: {user_data[chat_id]['location']}
🏢 Код об'єкта: {user_data[chat_id]['object_code']}
🏗️ Тип конструкції: {user_data[chat_id]['construction_type']}
📋 Завдання: {user_data[chat_id]['task']}
👷 Виконавець: {user_data[chat_id]['team']}
📸 Фото ДО: {photo_before_status}
📸 Фото ПІСЛЯ: {photo_after_status}
💬 Коментар: {comment}

Дані відправлено в систему!
"""
        
        markup = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, summary, reply_markup=markup)
        
        # Отправляем данные в Make.com
        send_to_make(bot, user_data[chat_id])
        
        # Очищаем данные пользователя
        del user_data[chat_id]

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    
    if chat_id not in user_data:
        bot.send_message(chat_id, "Натисніть /start щоб почати")
        return
    
    current_step = user_data[chat_id]["step"]
    
    # Обработка фото ДО
    if current_step == STEPS["PHOTO_BEFORE"]:
        photo_id = message.photo[-1].file_id
        user_data[chat_id]["photo_before"] = photo_id
        user_data[chat_id]["step"] = STEPS["PHOTO_AFTER"]
        
        # Кнопка для пропуска фото ПОСЛЕ
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Пропустити"))
        
        bot.send_message(
            chat_id, 
            "✅ Фото ДО отримано\n\n📸 Тепер надішліть фото ПІСЛЯ виконання робіт або натисніть 'Пропустити':",
            reply_markup=markup
        )
    
    # Обработка фото ПОСЛЕ
    elif current_step == STEPS["PHOTO_AFTER"]:
        photo_id = message.photo[-1].file_id
        user_data[chat_id]["photo_after"] = photo_id
        user_data[chat_id]["step"] = STEPS["COMMENT"]
        
        # Кнопка для пропуска комментария
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Пропустити"))
        
        bot.send_message(
            chat_id, 
            "✅ Фото ПІСЛЯ отримано\n\n💬 Додайте коментар або натисніть 'Пропустити':",
            reply_markup=markup
        )
    
    else:
        bot.send_message(chat_id, "❌ Зараз не потрібно надсилати фото")

# Функция отправки данных в Make.com
def send_to_make(bot, data):
    try:
        # Подготавливаем данные для отправки
        payload = {
            "date": data['date'],
            "location": data['location'],
            "object_code": data['object_code'],
            "construction_type": data['construction_type'],
            "task": data['task'],
            "team": data['team'],
            "comment": data['comment']
        }
        
        # Добавляем ссылки на фото, если они есть
        if data.get('photo_before'):
            payload['photo_before_url'] = bot.get_file_url(data['photo_before'])
        else:
            payload['photo_before_url'] = None
            
        if data.get('photo_after'):
            payload['photo_after_url'] = bot.get_file_url(data['photo_after'])
        else:
            payload['photo_after_url'] = None
        
        # Отправляем POST запрос
        response = requests.post(WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            print("✅ Дані успішно відправлено в Make.com")
        else:
            print(f"❌ Помилка відправки: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")

# Функция запуска бота с обработкой ошибок
def start_bot():
    while True:
        try:
            print("🤖 Бот запущено та готовий до роботи!")
            bot.polling(none_stop=True, timeout=10, long_polling_timeout=20)
        except requests.exceptions.ReadTimeout:
            print("❌ Timeout error: перезапуск бота через 5 секунд...")
            time.sleep(5)
        except requests.exceptions.ConnectionError:
            print("❌ Connection error: перезапуск бота через 10 секунд...")
            time.sleep(10)
        except telebot.apihelper.ApiTelegramException as e:
            if "409" in str(e):
                print("❌ Конфлікт: інший екземпляр бота вже працює. Зупиняємося...")
                break
            else:
                print(f"❌ Telegram API error: {e}, перезапуск через 15 секунд...")
                time.sleep(15)
        except Exception as e:
            print(f"❌ Unexpected error: {e}, перезапуск через 10 секунд...")
            time.sleep(10)

# Запуск бота
if __name__ == "__main__":
    start_bot()

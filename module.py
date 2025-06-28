import telebot
from telebot import types
import os

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(API_TOKEN)

# Меню
MAIN_MENU = {
    "🍕 Пицца": ["🍕 Маргарита", "🍕 Пепперони", "🍕 Четыре сыра"],
    "🍔 Бургер": ["🍔 Чизбургер", "🍔 Двойная котлета", "🍔 С беконом"],
    "🍟 Картошка": ["🍟 Фри", "🍟 По-деревенски"],
    "🥤 Напиток": ["🥤 Кола", "🥤 Фанта", "🧃 Сок"]
}

# Цены
ITEM_PRICES = {
    "🍕 Маргарита": 350,
    "🍕 Пепперони": 400,
    "🍕 Четыре сыра": 420,
    "🍔 Чизбургер": 250,
    "🍔 Двойная котлета": 300,
    "🍔 С беконом": 280,
    "🍟 Фри": 120,
    "🍟 По-деревенски": 150,
    "🥤 Кола": 100,
    "🥤 Фанта": 100,
    "🧃 Сок": 120
}

user_data = {}

# /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'order': [], 'total': 0}
    send_main_menu(chat_id)

def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in MAIN_MENU:
        markup.add(types.KeyboardButton(category))
    markup.add(types.KeyboardButton("✅ Готово"), types.KeyboardButton("🗑 Удалить позицию"))
    bot.send_message(chat_id, "👋 Добро пожаловать! Выберите категорию:", reply_markup=markup)

# Категория
@bot.message_handler(func=lambda message: message.text in MAIN_MENU)
def choose_category(message):
    category = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in MAIN_MENU[category]:
        price = ITEM_PRICES[item]
        button_text = f"{item} — {price}₽"
        markup.add(types.KeyboardButton(button_text))
    markup.add(types.KeyboardButton("🔙 Назад"), types.KeyboardButton("✅ Готово"))
    bot.send_message(message.chat.id, f"Вы выбрали {category}. Выберите блюдо:", reply_markup=markup)

# Позиция
@bot.message_handler(func=lambda message: any(name in message.text for name in ITEM_PRICES) and not message.text.startswith("❌ Удалить "))
def choose_item(message):
    chat_id = message.chat.id
    item = next((key for key in ITEM_PRICES if key in message.text), None)
    if not item:
        return

    user = user_data.setdefault(chat_id, {'order': [], 'total': 0})
    user['order'].append(item)
    user['total'] += ITEM_PRICES[item]
    bot.send_message(chat_id, f"{item} добавлен ✅\n💰 Сумма: {user['total']}₽")


# Назад
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_to_main(message):
    send_main_menu(message.chat.id)

# Удаление позиции
@bot.message_handler(func=lambda message: message.text == "🗑 Удалить позицию")
def delete_item(message):
    chat_id = message.chat.id
    user = user_data.get(chat_id)
    if not user or not user['order']:
        bot.send_message(chat_id, "❗ У вас нет позиций для удаления.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items_set = list(set(user['order']))
    for item in items_set:
        markup.add(types.KeyboardButton(f"❌ Удалить {item}"))
    markup.add(types.KeyboardButton("🔙 Назад"))
    bot.send_message(chat_id, "Выберите, что удалить из заказа:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.startswith("❌ Удалить "))
def confirm_delete(message):
    chat_id = message.chat.id
    item_to_delete = message.text.replace("❌ Удалить ", "")
    user = user_data.get(chat_id)

    if not user or not user['order']:
        bot.send_message(chat_id, "❗ У вас нет позиций для удаления.")
        return

    if item_to_delete in user['order']:
        user['order'].remove(item_to_delete)
        user['total'] -= ITEM_PRICES[item_to_delete]
        bot.send_message(chat_id, f"🗑 {item_to_delete} удалён.\n💰 Текущая сумма: {user['total']}₽")

        # Проверка, есть ли еще позиции
        if user['order']:
            delete_item(message)  # Снова показываем меню удаления
        else:
            bot.send_message(chat_id, "🛒 Ваш заказ теперь пуст.")
            send_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "❗ Такой позиции нет в вашем заказе.")


# Завершение заказа
@bot.message_handler(func=lambda message: message.text == "✅ Готово")
def finish_order(message):
    user = user_data.get(message.chat.id)
    if not user or not user['order']:
        bot.send_message(message.chat.id, "📦 Ваш заказ пуст.")
        return
    bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data[message.chat.id]['name'] = message.text
    bot.send_message(message.chat.id, "📍 Введите адрес доставки:")
    bot.register_next_step_handler(message, get_address)

def get_address(message):
    user_data[message.chat.id]['address'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Отправить номер", request_contact=True))
    bot.send_message(message.chat.id, "📱 Отправьте номер телефона:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    chat_id = message.chat.id
    user = user_data.get(chat_id)
    if not user:
        return

    user['phone'] = message.contact.phone_number

    # Группировка одинаковых позиций
    from collections import Counter
    counted_items = Counter(user['order'])
    order_text = "\n".join([f"{item} x{count}" for item, count in counted_items.items()])

    summary = (
        f"🧾 Новый заказ!\n"
        f"👤 Имя: {user['name']}\n"
        f"📞 Телефон: {user['phone']}\n"
        f"🏠 Адрес: {user['address']}\n"
        f"📦 Заказ:\n{order_text}\n"
        f"💰 Итого: {user['total']}₽"
    )

    # Клиенту
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("➕ Заказать ещё"))
    bot.send_message(chat_id, "✅ Спасибо за заказ! Ожидайте доставку.", reply_markup=markup)

    # Админу
    bot.send_message(ADMIN_ID, summary)

# Заказать ещё
@bot.message_handler(func=lambda message: message.text == "➕ Заказать ещё")
def order_again(message):
    user_data[message.chat.id] = {'order': [], 'total': 0}
    send_main_menu(message.chat.id)

# Запуск
bot.polling(none_stop=True)

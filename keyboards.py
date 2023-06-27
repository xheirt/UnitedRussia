import telebot
from telebot import types

edit_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
change_time_button = telebot.types.KeyboardButton('Изменить время')
change_date_button = telebot.types.KeyboardButton('Изменить дату')
cancel_button = telebot.types.KeyboardButton('Отмена')
edit_keyboard.add(change_time_button, change_date_button)
edit_keyboard.add(cancel_button)

reserv_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
delete_button = types.KeyboardButton("Удалить бронь")
back_button = types.KeyboardButton("Назад")
reserv_keyboard.add(delete_button, back_button)

commerce_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
button_yes = types.KeyboardButton('Да')
button_no = types.KeyboardButton('Нет')
commerce_keyboard.add(button_yes, button_no)

def create_main_keyboard(is_admin=False):
    reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    but1 = types.KeyboardButton('Забронировать помещение')
    but2 = types.KeyboardButton('Мои брони')
    but3 = types.KeyboardButton('Q&A')
    but4 = types.KeyboardButton('Связь с администратором')
    but5 = types.KeyboardButton('Просмотреть все бронирования')
    reply_keyboard.add(but1)
    reply_keyboard.add(but2)
    reply_keyboard.add(but3, but4)

    if is_admin:
        reply_keyboard.add(but5)

    return reply_keyboard
import os
import re

import telebot
import gspread
import datetime
from telebot import types
from datetime import datetime
import datetime as dt
from PIL import Image
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from keyboards import edit_keyboard, reserv_keyboard, commerce_keyboard, create_main_keyboard
from config import TOKEN, DOC_ID, COLUMN_HEADERS, WORKSHEET_NAME, RESERVATION_DATA, ADMINS

bot = telebot.TeleBot(TOKEN)

current_id = 1

#           #-- Ауетентификация --#

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)

#           #-- Создание кнопок --#

def create_keyboard(items):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(item) for item in items]
    keyboard.add(*buttons)
    return keyboard

#           #-- Обработка /start --#

@bot.message_handler(commands=['start'])
def start(message):
    admin = is_admin(message.from_user.id)
    keyboard = create_main_keyboard(admin)
    bot.send_message(message.chat.id, 'Здравствуйте!\nПожайлуйста, перед тем, как бронировать помещение заполните '
                                      'данный файл и отошлите на почту администратору\ntest@mail.ru  ', reply_markup=keyboard)
    bot.send_document(message.chat.id, open('test.docx', 'rb'))

#           #-- Верификация администратора --#

def is_admin(user_id):

    return user_id in ADMINS

#           #-- Обработка вывода бронирования --#

def view_all_reservations(message):
    sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)
    reservations = sheet.get_all_records()

    if reservations:
        reservation_text = '\n\n'.join([f'Дата бронирования: {r["reservation_date"]}\n'
                                        f'Организатор: {r["organizer_name"]}\n'
                                        f'Дата создания: {r["creation_date"]}\n'
                                        f'Номер телефона: {r["phone_number"]}\n'
                                        f'Количество людей: {r["people"]}\n'
                                        f'Название: {r["event_name"]}\n'
                                        f'Тематика: {r["theme"]}\n'
                                        f'ID брони: {str(r["id"])}' for r in reservations])
        bot.send_message(message.chat.id, f'Все бронирования:\n\n{reservation_text}')
    else:
        bot.send_message(message.chat.id, 'Пока нет ни одного бронирования.')

#           #-- Обработка сообщений --#

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == 'Забронировать помещение':
        keyboard = create_keyboard(['Отмена'])
        bot.send_message(message.chat.id, 'Выберите дату бронирования (DD.MM.YYYY):', reply_markup=keyboard)
        bot.register_next_step_handler(message, confirm_reservation)
    elif message.text == 'Отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=reply_keyboard)
    elif message.text == 'Назад':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=reply_keyboard)
    elif message.text == 'Мои брони':
        sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)
        reservations = sheet.get_all_records()

        user_reservations = [r for r in reservations if r['user_id'] == message.from_user.id]

        if user_reservations:
            reservation_text = '\n\n'.join([f'Дата бронирования: {r["reservation_date"]}\n'
                                            f'Организатор: {r["organizer_name"]}\n'
                                            f'Дата создания: {r["creation_date"]}\n'
                                            f'Номер телефона: {r["phone_number"]}\n'
                                            f'Количество людей: {r["people"]}\n'
                                            f'Название: {r["event_name"]}\n'
                                            f'Тематика: {r["theme"]}\n'
                                            f'ID брони: {str(r["id"])}' for r in user_reservations])
            bot.send_message(message.chat.id, f'Ваши бронирования:\n\n{reservation_text}')
            bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=reserv_keyboard)
        else:
            bot.send_message(message.chat.id, 'У вас пока нет ни одного бронирования.')
    elif message.text.startswith('Удалить бронь'):
        if is_admin(message.from_user.id):
            bot.send_message(message.chat.id, 'Введите ID бронирования для удаления:')
            bot.register_next_step_handler(message, delete_reservation_by_id_admin)
        else:
            bot.send_message(message.chat.id, 'Введите ID бронирования для удаления:')
            bot.register_next_step_handler(message, delete_reservation_by_id)
    elif message.text == 'Просмотреть все бронирования':
        view_all_reservations(message)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=reserv_keyboard)
    elif message.text == 'Q&A':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Фотографии лофта', callback_data='button1'))
        keyboard.add(types.InlineKeyboardButton('Правила', callback_data='button2'))
        bot.send_message(message.chat.id,
                         'Добро пожаловать в наш Лофт! \n\nЗдесь вы можете почувствовать себя как дома и провести время с удовольствием',
                         reply_markup=keyboard)
    elif message.text == 'Связь с администратором':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'По оставшимся вопросам можете связаться с администратором:\n 8 (951) 843-48-17 - Игорь', reply_markup=reply_keyboard)
    else:
        bot.send_message(message.chat.id, 'Извините, я не понимаю, что вы хотите сделать. Пожалуйста, выберите одно из действий на клавиатуре.')

#           #-- Q&A --#

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'button1':
        back_keyboard = types.InlineKeyboardMarkup()
        back_keyboard.add(types.InlineKeyboardButton('Назад', callback_data='back'))

        album = []
        for i in range(1, 8):
            photo_path = os.path.join(os.getcwd(), f'images/{i}.jpg')
            with open(photo_path, 'rb') as photo_file:
                photo_data = photo_file.read()
                album.append(types.InputMediaPhoto(photo_data))

        bot.send_media_group(call.message.chat.id, album)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == 'button2':
        back_keyboard = types.InlineKeyboardMarkup()
        back_keyboard.add(types.InlineKeyboardButton('Назад', callback_data='back'))

        bot.send_message(call.message.chat.id, 'Правила:\n\n1. Запрещено курение в помещении.\n'
                                               '2. Нельзя выносить оборудование на улицу.\n\n'
                                               'Организация площадки для проведения мероприятий так же входит в забронированные часы\n'
                                               'Если у вас есть вопросы, обратитесь к администратору.',
                         reply_markup=back_keyboard)

        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == 'back':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Фотографии лофта', callback_data='button1'))
        keyboard.add(types.InlineKeyboardButton('Правила', callback_data='button2'))

        bot.send_message(call.message.chat.id, 'Добро пожаловать в наш Лофт! \n\nЗдесь вы можете почувствовать себя как дома и провести время с удовольствием', reply_markup=keyboard)

        bot.delete_message(call.message.chat.id, call.message.message_id)

#           #-- Удаление бронирования --#

def delete_reservation_by_id(message):
    reservation_id = message.text

    sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)
    reservations = sheet.get_all_records()

    deleted = False

    for row in reservations:
        if str(row['id']) == reservation_id and row['user_id'] == message.chat.id:
            sheet.delete_row(reservations.index(row) + 2)  # +2 для учета заголовков в таблице
            deleted = True
            break

    if deleted:
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, f'Бронь с ID {reservation_id} удалена.', reply_markup=reply_keyboard)
    else:
        bot.send_message(message.chat.id, f'Бронь с ID {reservation_id} не найдена.')

#           #-- Удаление бронирования администратором --#

def delete_reservation_by_id_admin(message):
    reservation_id = message.text

    sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)
    reservations = sheet.get_all_records()

    deleted = False

    for row in reservations:
        if str(row['id']) == reservation_id:
            sheet.delete_row(reservations.index(row) + 2)  # +2 для учета заголовков в таблице
            deleted = True
            break

    if deleted:
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, f'Бронь с ID {reservation_id} удалена.', reply_markup=reply_keyboard)
    else:
        bot.send_message(message.chat.id, f'Бронь с ID {reservation_id} не найдена.')

#           #-- Добавление админ-клавиши --#

def add_view_all_reservations_button(reply_keyboard, is_admin):
    if is_admin:
        reply_keyboard.add(types.KeyboardButton('Просмотреть все бронирования'))
    return reply_keyboard

#           #-- Заполнение словаря --#

def confirm_reservation(message):
    global current_id
    if message.text == 'Отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Бронирование отменено.', reply_markup=reply_keyboard)
    else:
        RESERVATION_DATA['id'] = current_id
        RESERVATION_DATA['user_id'] = message.chat.id
        RESERVATION_DATA['reservation_date'] = None
        RESERVATION_DATA['reservation_time'] = None
        RESERVATION_DATA['organizer_name'] = None
        RESERVATION_DATA['event_name'] = None
        RESERVATION_DATA['theme'] = None
        RESERVATION_DATA['people'] = None
        RESERVATION_DATA['creation_date'] = datetime.now().strftime("%d.%m.%Y, %H:%M")
        RESERVATION_DATA['phone_number'] = None
        RESERVATION_DATA['start_time'] = None
        RESERVATION_DATA['end_time'] = None
        RESERVATION_DATA['commerce'] = None

        current_id += 1

        reservation_date = message.text.strip()
        if not is_valid_date(reservation_date):
            bot.send_message(message.chat.id, 'Неправильный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ')
            bot.register_next_step_handler(message, confirm_reservation)
            return

        RESERVATION_DATA['reservation_date'] = reservation_date

        bot.send_message(message.chat.id, 'Введите время начала бронирования в формате ЧЧ:ММ: ')
        bot.register_next_step_handler(message, save_reservation_time, RESERVATION_DATA)

#           #-- Запись времени начала бронирования --#

def save_reservation_time(message, reservation_data):
    reservation_time = message.text.strip()

    if reservation_time.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    time_pattern = r'^([01]\d|2[0-3]):([0-5]\d)$'
    if not re.match(time_pattern, reservation_time):
        bot.send_message(message.chat.id, 'Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.')
        bot.register_next_step_handler(message, save_reservation_time, reservation_data)
        return

    hours, minutes = map(int, reservation_time.split(':'))
    start_time = dt.time(9, 0)
    end_time = dt.time(22, 0)
    selected_time = dt.time(hours, minutes)

    if selected_time < start_time or selected_time > end_time:
        bot.send_message(message.chat.id,
                         'Выбранное время не входит в допустимый диапазон (09:00 - 22:00). Пожалуйста, выберите другое время.')
        bot.register_next_step_handler(message, save_reservation_time, reservation_data)
        return

    reservation_data['start_time'] = selected_time.strftime('%H:%M')
    print(reservation_data)
    bot.send_message(message.chat.id, 'Введите время окончания бронирования в формате ЧЧ:ММ: ')
    bot.register_next_step_handler(message, save_end_time, reservation_data)

#           #-- Запись времени окончания бронирования --#

def save_end_time(message, reservation_data):
    end_time = message.text.strip()

    if end_time.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    # Проверка формата времени
    time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(time_pattern, end_time):
        bot.send_message(message.chat.id, 'Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.')
        bot.register_next_step_handler(message, save_end_time, reservation_data)
        return

    hours, minutes = map(int, end_time.split(':'))

    start_time = dt.time(9, 0)
    end_time_range = dt.time(22, 0)
    selected_end_time = dt.time(hours, minutes)

    if selected_end_time < start_time or selected_end_time > end_time_range:
        bot.send_message(message.chat.id,
                         'Выбранное время не входит в допустимый диапазон (09:00 - 22:00). Пожалуйста, выберите другое время.')
        bot.register_next_step_handler(message, save_end_time, reservation_data)
        return

    start_hours, start_minutes = map(int, reservation_data['start_time'].split(':'))
    start_time = dt.time(start_hours, start_minutes)

    if selected_end_time <= start_time:
        bot.send_message(message.chat.id,
                         'Время окончания бронирования должно быть позже времени начала. Пожалуйста, выберите другое время.')
        bot.register_next_step_handler(message, save_end_time, reservation_data)
        return

    reservation_data['end_time'] = selected_end_time.strftime('%H:%M')
    reservation_data['reservation_time'] = reservation_data['start_time'] + ' - ' + reservation_data['end_time']

    result = is_time_slot_available(reservation_data['reservation_date'], reservation_data['start_time'],
                                    reservation_data['end_time'])
    if result is not None:
        bot.send_message(message.chat.id, result, reply_markup=edit_keyboard)
        bot.register_next_step_handler(message, handle_edit_time_or_date)
        return

    print(reservation_data)
    bot.send_message(message.chat.id, 'Введите ФИО организатора:')
    bot.register_next_step_handler(message, save_organizer_name, reservation_data)

#           #-- Запись имени организатора --#

def save_organizer_name(message, reservation_data):
    organizer_name = message.text.strip()

    if organizer_name.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    if not validate_fio(message.text):
        bot.send_message(message.chat.id, 'Вы ввели некорректное ФИО. Пожалуйста, введите ФИО в формате "Фамилия Имя Отчество".')
        bot.register_next_step_handler(message, save_organizer_name, reservation_data)
        return

    reservation_data['organizer_name'] = organizer_name

    bot.send_message(message.chat.id, 'Введите номер телефона организатора:')
    bot.register_next_step_handler(message, save_phone_number, reservation_data)

#           #-- Запись телефона организатора --#

def save_phone_number(message, reservation_data):
    phone_number = message.text.strip()

    if phone_number.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    phone_regex = r'^((\+7|7|8)+([0-9]){10})$'
    if not re.match(phone_regex, phone_number):
        bot.send_message(message.chat.id, 'Номер телефона введен в неправильном формате. Пожалуйста, введите номер телефона в формате +7XXXXXXXXXX:')
        bot.register_next_step_handler(message, save_phone_number, reservation_data)
        return

    reservation_data['phone_number'] = phone_number

    bot.send_message(message.chat.id, 'Введите название мероприятия:')
    bot.register_next_step_handler(message, save_event_name, reservation_data)

#           #-- Запись названия мероприятия --#

def save_event_name(message, reservation_data):
    event_name = message.text.strip()
    if event_name.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    reservation_data['event_name'] = event_name

    bot.send_message(message.chat.id, 'Какая будет тематика мероприятия?')
    bot.register_next_step_handler(message, save_theme_name, reservation_data)

#           #-- Запись тематики мероприятия --#

def save_theme_name(message, reservation_data):
    theme_name = message.text.strip()
    if theme_name.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return
    reservation_data['theme'] = theme_name

    bot.send_message(message.chat.id, 'Является ли мероприятие коммерческим? ',  reply_markup=commerce_keyboard)
    bot.register_next_step_handler(message, save_commerce, reservation_data)

#           #-- Подтверждение коммерческого мероприятия --#

def save_commerce(message, reservation_data):
    commerce_value = message.text.strip()

    if commerce_value.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    RESERVATION_DATA['commerce'] = commerce_value

    bot.send_message(message.chat.id, 'Введите количество человек на мероприятии:', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, save_people_count, reservation_data, commerce_value)

#           #-- Запись колличества человек --#

def save_people_count(message, reservation_data, commerce_value):
    people_count = message.text.strip()

    if people_count.lower() == 'отмена':
        admin = is_admin(message.from_user.id)
        reply_keyboard = create_main_keyboard(admin)
        bot.send_message(message.chat.id, 'Операция отменена.', reply_markup=reply_keyboard)
        return

    if not people_count.isnumeric():
        bot.send_message(message.chat.id, 'Количество человек должно быть числом. Пожалуйста, попробуйте еще раз:')
        bot.register_next_step_handler(message, save_people_count, reservation_data, commerce_value)
        return

    reservation_data['people'] = int(people_count)
    reservation_data['commerce'] = 'Да' if commerce_value.lower() == 'да' else 'Нет'

    sheet.append_row(list(reservation_data.values()))

    admin = is_admin(message.from_user.id)
    reply_keyboard = create_main_keyboard(admin)
    bot.send_message(message.chat.id, f'Вы забронировали помещение на {reservation_data["reservation_date"]} число на {reservation_data["reservation_time"]},\n'
                                      f'Организатор: {reservation_data["organizer_name"]}\n'
                                      f'Количество людей: {reservation_data["people"]}\n'
                                      f'Телефон для связи: {reservation_data["phone_number"]}\n'
                                      f'Название: {reservation_data["event_name"]} и тематика: {reservation_data["theme"]}\n'
                                      f'ID бронирования: {reservation_data["id"]}',
                     reply_markup=reply_keyboard)
    bot.send_message(message.chat.id, 'Правила использования помещения:\n'
                                      '- Нельзя выносить оборудование на улицу.\n'
                                      '- Запрещено курение в помещении.\n'
                                      '- После мероприятия необходимо убрать мусор и оставить помещение в чистоте.\n'
                                      'Организация площадки для проведения мероприятий также входит в забронированные часы\nЕсли у вас есть вопросы, обратитесь к администратору.',
                     reply_markup=reply_keyboard)

#           #-- Получение списка временных слотов --#

def get_available_time_slots(reservation_date):
    global sheet

    values = sheet.get_all_values()
    existing_time_slots = []

    for row in values:
        if row[2] == reservation_date and row[10] is not None and row[11] is not None:
            existing_start_time = datetime.strptime(row[10], "%H:%M").time()
            existing_end_time = datetime.strptime(row[11], "%H:%M").time()
            existing_time_slots.append(
                f"{existing_start_time.strftime('%H:%M')} - {existing_end_time.strftime('%H:%M')}")

    return existing_time_slots

#           #-- Проверка доступности временного слота --#

def is_time_slot_available(reservation_date, start_time, end_time):
    global sheet

    values = sheet.get_all_values()
    for row in values:
        if (
                row[2] == reservation_date and
                row[10] is not None and
                row[11] is not None
        ):
            existing_start_time = datetime.strptime(row[10], "%H:%M").time()
            existing_end_time = datetime.strptime(row[11], "%H:%M").time()

            start_time_dt = datetime.strptime(start_time, "%H:%M").time()
            end_time_dt = datetime.strptime(end_time, "%H:%M").time()

            if (
                    start_time_dt < existing_end_time and
                    end_time_dt > existing_start_time
            ):
                available_time_slots = get_available_time_slots(reservation_date)
                message = 'Выбранное время уже забронировано. Пожалуйста, выберите другое время.\n\nУже забронированные временные слоты:\n'
                message += '\n'.join(available_time_slots)
                return message

    return None

#           #-- Обработчки сообщений при занятом слоте --#

def handle_edit_time_or_date(message):
    if message.text == 'Изменить время':
        keyboard = create_keyboard(['Отмена'])
        bot.send_message(message.chat.id, 'Выберите новое время бронирования (ЧЧ:ММ):', reply_markup=keyboard)
        bot.register_next_step_handler(message, save_reservation_time, RESERVATION_DATA)
    elif message.text == 'Изменить дату':
        keyboard = create_keyboard(['Отмена'])
        bot.send_message(message.chat.id, 'Выберите новую дату бронирования (DD.MM.YYYY):', reply_markup=keyboard)
        bot.register_next_step_handler(message, confirm_reservation)
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=edit_keyboard)
    else:
        bot.send_message(message.chat.id, 'Извините, я не понимаю, что вы хотите сделать. Пожалуйста, выберите одну из доступных опций.')

#           #-- Получение данных --#

def get_spreadsheet():
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets().get(spreadsheetId=DOC_ID).execute()
    sheet_title = sheet['properties']['title']
    sheet_values = sheet['sheets'][0]['properties']['gridProperties']['rowCount']
    sheet_range = sheet_title + '!A1:M' + str(sheet_values)

    if not sheet['sheets'][0]['data']:
        sheet_body = {
            'range': sheet_range,
            'values': [COLUMN_HEADERS]
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=DOC_ID, range=sheet_range,
            valueInputOption='USER_ENTERED', body=sheet_body).execute()

    return sheet

#           #-- Валидация ФИО --#

def validate_fio(fio):
    fio_regex = r'^[А-ЯЁа-яё]+\s[А-ЯЁа-яё]+\s[А-ЯЁа-яё]+$'
    if re.match(fio_regex, fio):
        return True
    else:
        return False

#           #-- Валидация даты --#

def is_valid_date(date_str):
    try:
        dt.datetime.strptime(date_str, '%d.%m.%Y')
        return True
    except ValueError:
        return False

bot.polling(none_stop=True)




"""
# Функция для изменения бронирования по ID
def edit_reservation_by_id(message):
    reservation_id = message.text

    # Получаем все бронирования из Google Sheets
    sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)
    reservations = sheet.get_all_records()

    found_reservations = [row for row in reservations if str(row['id']) == reservation_id and row['user_id'] == message.chat.id]

    if found_reservations:
        reservation = found_reservations[0]

        # Выводим список пунктов для изменения
        edit_options = {
            1: ("Дата", "reservation_date"),
            2: ("Время", "reservation_time"),
            3: ("Организатор", "organizer_name"),
            4: ("Название", "event_name"),
            5: ("Тема", "theme"),
            6: ("Кол-во людей", "people"),
            7: ("Телефон", "phone_number")
        }
        edit_options_text = '\n'.join([f'{option_num}. {option[0]}' for option_num, option in edit_options.items()])
        bot.send_message(message.chat.id, f'Выберите пункт для изменения:\n{edit_options_text}')
        bot.register_next_step_handler(message, edit_reservation_property, reservation, edit_options)
    else:
        bot.send_message(message.chat.id, f'Бронь с ID {reservation_id} не найдена.')

# Функция для изменения свойства бронирования
def edit_reservation_property(message, reservation, edit_options):
    selected_option = message.text.strip()

    if selected_option.isdigit() and int(selected_option) in edit_options:
        property_name, property_key = edit_options[int(selected_option)]

        # Просим пользователя ввести новое значение для свойства
        bot.send_message(message.chat.id, f'Введите новое значение для "{property_name}":')
        bot.register_next_step_handler(message, update_reservation_property, reservation, property_key)
    else:
        bot.send_message(message.chat.id, 'Неверный выбор. Пожалуйста, выберите номер пункта для изменения.')

# Функция для обновления свойства бронирования
def update_reservation_property(message, reservation, property_key):
    new_value = message.text.strip()

    # Обновляем свойство бронирования в Google Sheets
    sheet = client.open_by_key(DOC_ID).worksheet(WORKSHEET_NAME)

    reservation[property_key] = new_value
    sheet.update([reservation], value_input_option='USER_ENTERED')

    bot.send_message(message.chat.id, f'Свойство "{property_key}" успешно изменено.')
"""
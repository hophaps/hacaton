# основной файл запуска бота и работы с методами
from langchain_core.prompts import ChatPromptTemplate  # Импортируем шаблоны для общения с ботом
from langchain_core.output_parsers import StrOutputParser  # Импортируем парсер для вывода строк
from langchain_community.chat_models.gigachat import GigaChat  # Импортируем модель GigaChat
import webbrowser  # Импортируем модуль для работы с веб-браузером
import config  # Импортируем конфигурацию (например, токены и настройки)
from data import db  # Импортируем базу данных
from telebot import types  # Импортируем типы для работы с клавиатурой в Telegram
from telebot.types import ReplyKeyboardMarkup  # Импортируем разметку для ответной клавиатуры

import re  # Для работы с регулярными выражениями
from lecture_processing import download_from_yandex_disk  # Импортируем функцию для загрузки с Яндекс.Диска
import threading  # Для работы с потоками
import time  # Для управления временем и задержками

import telebot  # Импортируем библиотеку для работы с Telegram API
import sqlite3  # Импортируем библиотеку для работы с SQLite

# Инициализация бота с использованием токена из конфигурации
bot = telebot.TeleBot(config.TG_BOT_TOKEN)

# Инициализация модели GigaChat с переданными учетными данными
model = GigaChat(
    credentials=config.API_GIGA_TOKEN,  # Токен для доступа к GigaChat API
    scope=config.API_GIGA_VERS,  # Версия API
    model=config.API_GIGA_MODEL,  # Модель для использования
    verify_ssl_certs=False  # Отключаем проверку SSL-сертификатов
)

# Глобальная переменная для режима study_buddy
study_buddy_mode = {}


def generate_command_keyboard():
    """
    Функция для генерации клавиатуры с командами.
    Возвращает клавиатуру с кнопками для различных команд бота.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)  # Создаем разметку клавиатуры с возможностью изменения размера
    # Создаем кнопки для каждой команды
    buttons = [
        "/site",
        "/where_am_I",
        "/study_buddy",
        "/activities",
        "/news",
        "/goroscop",
        "/freetime",
        "/anekdot"
    ]

    # Добавляем кнопки в клавиатуру парами
    for i in range(0, 8, 2):
        keyboard.add(types.KeyboardButton(buttons[i]), types.KeyboardButton(buttons[i - 1]))

    return keyboard  # Возвращаем готовую клавиатуру


def make_request_toGIGACHAT(input_promt, input_text):
    """
    Функция для отправки запроса к модели GigaChat и получения ответа.
    input_promt - системный шаблон, input_text - текст от пользователя.
    """
    system_template = "{sys_promt}"  # Шаблон для системного сообщения
    prompt_template = ChatPromptTemplate.from_messages([  # Создаем шаблон сообщений для общения с моделью
        ('system', system_template),
        ('user', '{user_text}')
    ])
    parser = StrOutputParser()  # Создаем парсер для обработки строки ответа
    chain = prompt_template | model | parser  # Создаем цепочку обработки запроса
    result = chain.invoke({"sys_promt": input_promt, "user_text": input_text})  # Отправляем запрос и получаем ответ
    return result  # Возвращаем результат


# Глобальная переменная для режима where_am_i
where_am_i_mode = {}


@bot.message_handler(commands=['where_am_I'])  # Обработчик команды /where_am_I
def where_am_i(message):
    """
    Функция, которая вызывается при команде /where_am_I.
    Отображает клавиатуру с выбором факультетов.
    """
    global where_am_i_mode  # Объявляем, что будем использовать глобальную переменную
    user_id = message.chat.id  # Получаем ID пользователя
    study_buddy_mode[user_id] = True  # Устанавливаем режим study_buddy для пользователя
    keyboard = types.InlineKeyboardMarkup()  # Создаем инлайн-клавиатуру

    # Добавляем кнопки для выбора факультетов с соответствующими callback данными
    keyboard.add(
        types.InlineKeyboardButton("01, Факультет строительства и экологии (ФСиЭ)",
                                   callback_data='52.032045,113.529696'),
        types.InlineKeyboardButton("02, Факультет экономики и управления (ФЭиУ)", callback_data='52.035253,113.528196')
    )
    keyboard.add(
        types.InlineKeyboardButton("03, Энергетический факультет (ЭФ)", callback_data='52.034577,113.529777'),
        types.InlineKeyboardButton("05, Факультет строительства и экологии (ФСиЭ)",
                                   callback_data='52.023961,113.512413')
    )
    keyboard.add(
        types.InlineKeyboardButton("06, Горный факультет (ГФ)", callback_data='52.036034,113.510149'),
        types.InlineKeyboardButton("07, Юридический факультет (ЮФ)", callback_data='52.031901,113.525025')
    )
    keyboard.add(
        types.InlineKeyboardButton("10, Историко-филологический факультет (ИФФ)", callback_data='52.037635,113.501840'),
        types.InlineKeyboardButton("11, Факультет культуры и искусств (ФКиИ)", callback_data='52.038411,113.501965')
    )
    keyboard.add(
        types.InlineKeyboardButton("12, Факультет физической культуры и спорта (ФФКиС)",
                                   callback_data='52.038455,113.500834'),
        types.InlineKeyboardButton("13, Историко-филологический факультет (ИФФ)", callback_data='52.037973,113.503160')
    )
    keyboard.add(
        types.InlineKeyboardButton("14, Социологический факультет (СФ)", callback_data='52.039314,113.499648'),
        types.InlineKeyboardButton("22, Физкультурно-оздоровительный комплекс (ФОК)",
                                   callback_data='52.033674,113.528789')
    )

    # Отправляем сообщение пользователю с предложением выбрать факультет
    bot.send_message(message.chat.id, "Выберите факультет, в которой нужно добраться:", reply_markup=keyboard)


# Обработчик нажатий на кнопки инлайн-клавиатуры
@bot.callback_query_handler(func=lambda call: True)
def button_handler(call):
    """
    Обрабатывает нажатие кнопки на клавиатуре.
    Извлекает координаты из данных кнопки и отправляет местоположение в чат.
    """
    latitude, longitude = map(float, call.data.split(","))  # Извлекаем широту и долготу из данных кнопки
    location = types.Location(latitude=latitude, longitude=longitude)  # Создаем объект локации
    bot.send_location(call.message.chat.id, latitude, longitude)  # Отправляем местоположение в чат


# Обработчик команды /goroscop
@bot.message_handler(commands=['goroscop'])
def output_goroskop(message):
    """
    Обрабатывает команду /goroscop.
    Отправляет сообщение о начале работы и запрашивает гороскоп для всех знаков зодиака.
    """
    bot.send_message(message.chat.id, "Устанавливаю связь с космосом...\nПодождите...")  # Уведомление пользователю
    bot.send_chat_action(message.chat.id, 'typing')  # Показывает индикатор печати
    # Запрашиваем гороскоп для всех знаков зодиака с помощью модели GigaChat
    bot.send_message(message.chat.id, make_request_toGIGACHAT(
        "ты составитель текстовых гороскопов по формату знак зодиака, совет, пожелания",
        "составь гороскоп для всех знаков зодиака"), reply_markup=generate_command_keyboard())  # Отправляем результат


# Обработчик команды /news
@bot.message_handler(commands=['news'])
def get_last_news(message):
    """
    Обрабатывает команду /news.
    Извлекает последние новости из базы данных и отправляет их пользователю.
    """
    bot.send_message(message.chat.id, "Так, посмотрим...")  # Уведомление пользователю о начале обработки
    bot.send_chat_action(message.chat.id, 'typing')  # Показывает индикатор печати
    connection_ = sqlite3.connect('news.db')  # Подключаемся к базе данных новостей
    cursor_ = connection_.cursor()  # Создаем курсор для выполнения SQL-запросов
    cursor_.execute('SELECT * FROM NEWS where interests = ?', ('tech',))  # Извлекаем новости по интересу "технологии"
    news = cursor_.fetchall()  # Получаем все результаты запроса
    newsrep = news[len(news) - 1][2]  # Получаем текст последней новости
    newsrep = newsrep[:250]  # Обрезаем текст до 250 символов
    newsrep = make_request_toGIGACHAT("обработай следующий текст", newsrep)  # Обрабатываем текст с помощью GigaChat
    bot.send_message(message.chat.id, newsrep)  # Отправляем обработанный текст пользователю
    bot.send_chat_action(message.chat.id, 'typing')  # Показывает индикатор печати
    bot.send_message(message.chat.id, news[len(news) - 1][3],
                     reply_markup=generate_command_keyboard())  # Отправляем дополнительную информацию о новости

    connection_.commit()  # Подтверждаем изменения (хотя здесь это не обязательно)
    connection_.close()  # Закрываем соединение с базой данных


# Обработчик команды /freetime
@bot.message_handler(commands=['freetime'])
def output_freetime(message):
    """
    Обрабатывает команду /freetime.
    Извлекает расписание пользователя и определяет свободное время.
    """
    user_id = 88005553535  # Задаем ID пользователя (можно сделать динамическим)
    date = "29.10"  # Задаем дату для запроса расписания
    connection = sqlite3.connect('raspisanie.db')  # Подключаемся к базе данных расписания
    cursor = connection.cursor()  # Создаем курсор для выполнения SQL-запросов
    cursor.execute('SELECT * FROM time')  # Извлекаем все записи расписания
    users = cursor.fetchall()  # Получаем все результаты запроса
    for user in users:
        # Проверяем, соответствует ли ID пользователя и дата
        if user[1] == user_id and user[2] == date:
            # Формируем строку с информацией о занятиях
            user_inp = "уроки - " + str(user[3]) + " Спортивная секция - " + str(user[4]) + " Время сна " + str(user[5])
            bot.send_message(message.chat.id, ("Занятия сегодня " + user_inp))  # Отправляем информацию о занятиях
            bot.send_chat_action(message.chat.id, 'typing')  # Показывает индикатор печати
            # Запрашиваем свободное время на основе расписания
            free_time_str = make_request_toGIGACHAT(
                "проанализируй следующее расписание и напиши промежутки свободного времени: ",
                user_inp)
            bot.send_message(message.chat.id, free_time_str)  # Отправляем информацию о свободном времени
    connection.commit()  # Подтверждаем изменения (хотя здесь это не обязательно)
    connection.close()  # Закрываем соединение с базой данных
    bot.send_message(message.chat.id, f'Дайтека подумать что я могу вам посоветовать...')  # Сообщаем о процессе
    bot.send_chat_action(message.chat.id, 'typing')  # Показывает индикатор печати
    # Запрашиваем рекомендации на основе свободного времени
    bot.send_message(message.chat.id, make_request_toGIGACHAT(
        "проанализируй !свободное !время из следующего предложения и напиши !краткие рекомендации из !5 !пунктов чтобы провести !свободное !время для !студента, который интересуется !информатикой и !технологиями.",
        free_time_str), reply_markup=generate_command_keyboard())  # Отправляем рекомендации


# Обработчик команды /test
@bot.message_handler(commands=['test'])
def test(message):
    """
    Обрабатывает команду /test.
    Отправляет ID пользователя в чат для тестирования.
    """
    tg_id = message.chat.id  # Получаем ID пользователя
    bot.send_message(message.chat.id, tg_id)  # Отправляем ID обратно пользователю


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help(message):
    """
    Обрабатывает команду /help.
    Отправляет пользователю информацию о помощи.
    """
    bot.send_message(message.chat.id, config.HELP_INFORMATION,
                     reply_markup=generate_command_keyboard())  # Отправляем информацию о помощи


# Хранилище состояний пользователей
user_states = {}

# Состояние, показывающее, что пользователь должен ввести свой ID
ASKING_FOR_ID = "ASKING_FOR_ID"


# Обработчик команд /start, /main, /hello
@bot.message_handler(commands=['start', 'main', 'hello'])
def main(message):
    """
    Обрабатывает команды /start, /main и /hello.
    Проверяет авторизацию пользователя и предоставляет доступ к функционалу бота.
    """
    tg_id = message.chat.id  # Получаем ID пользователя
    user_data = db.get_user_by_tg_id(tg_id)  # Получаем данные пользователя из базы данных

    # Если пользователь уже авторизован, сразу предоставляем доступ
    if user_data and user_data.is_authorized:
        role = user_data.role  # Получаем роль пользователя
        bot.send_message(message.chat.id, f'Привет снова, {message.from_user.first_name}!',
                         reply_markup=generate_command_keyboard())  # Приветствие пользователя
        bot.send_message(message.chat.id, f'Ваш статус: {role}')  # Информируем о статусе

        if role == "admin":  # Если пользователь администратор
            bot.send_message(message.chat.id, config.HELP_INFORMATION)  # Отправляем информацию о помощи
        return  # Завершаем выполнение функции

    # Если пользователя нет в базе или он не авторизован, запрашиваем ID
    bot.send_message(message.chat.id,
                     f'Привет, {message.from_user.first_name}, введите, пожалуйста, свой ID:')  # Запрос ID
    user_states[tg_id] = ASKING_FOR_ID  # Устанавливаем состояние ожидания ID


# Обработчик сообщений для ожидания ввода ID пользователя
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == ASKING_FOR_ID)
def authorize_user(message):
    """
    Обрабатывает ввод ID пользователя, проверяет его корректность и авторизует пользователя.
    """
    tg_id = message.chat.id  # Получаем ID чата Telegram
    user_id = message.text.strip()  # Извлекаем текст сообщения (ввод пользователя) и удаляем пробелы

    # Проверка на числовой ввод
    if not user_id.isdigit():  # Если введенный ID не является числом
        bot.send_message(message.chat.id, "Пожалуйста, введите действительный числовой ID.")  # Сообщаем пользователю
        return

    user_id = int(user_id)  # Преобразуем введенный ID в целое число

    # Проверка на совпадение ID с tg_id
    if user_id == tg_id:  # Если введенный ID совпадает с ID Telegram
        if db.get_role_by_user_id(tg_id) == "admin":  # Если пользователь администратор
            bot.send_message(message.chat.id, config.NEWS_FORM)  # Отправляем форму новостей
        user_states.pop(tg_id, None)  # Удаляем состояние ожидания, так как ID введен верно
        return

    # Проверка на наличие пользователя в базе
    if db.get_user_by_id(user_id):  # Если пользователь существует в базе данных
        # Добавляем Telegram ID в базу данных и отмечаем пользователя как авторизованного
        db.add_tg_id(user_id, tg_id, is_authorized=True)

        # Приветственное сообщение для авторизованного пользователя
        bot.send_message(message.chat.id, config.SECOND_WELCOME_PHRASE)  # Отправляем вторичное приветствие
        bot.send_message(message.chat.id, f'Ваш tg ID: {tg_id}')  # Сообщаем пользователю его tg ID
        bot.send_message(message.chat.id,
                         f'Ваш статус: {db.get_role_by_user_id(tg_id)}')  # Сообщаем статус пользователя

        # Удаляем состояние после успешной авторизации
        user_states.pop(tg_id, None)  # Удаляем состояние ожидания

        # Возвращаем интересы пользователя
        nw = db.get_interest(tg_id)  # Получаем интересы пользователя
        return nw  # Возвращаем интересы (пока не используем это значение)
    else:
        # Если учетной записи пользователя нет
        bot.send_message(
            message.chat.id,
            "Возможно, вы ошиблись. Если нет, то вашей учетной записи не существует. Обратитесь к администрации."
        )  # Сообщаем пользователю о неверном ID
        # Сохраняем состояние ожидания, так как ID был неверный


# Обработчик команды /site
@bot.message_handler(commands=['site'])
def site(message):
    """
    Открывает веб-сайт по указанному URL.
    """
    webbrowser.open('https://xn--80acgn7d.xn--p1ai/')  # Открываем указанный сайт


# Обработчик команды /anekdot
@bot.message_handler(commands=['anekdot'])
def generate_anekdot(message):
    """
    Генерирует анекдот с помощью GigaChat и отправляет его пользователю.
    """
    bot.send_chat_action(message.chat.id, 'typing')  # Показываем индикатор печати
    # Запрашиваем анекдот у GigaChat
    bot.send_message(message.chat.id, make_request_toGIGACHAT("ты генератор добрых анекдотов для студентов.",
                                                              "напиши анекдот"),
                     reply_markup=generate_command_keyboard())  # Отправляем анекдот


# Функция для мониторинга флагов
def monitor_flag():
    """
    Следит за статусом публикации лекций и отправляет их в канал.
    """
    CHANNEL_ID = config.CHANNEL_NAME  # Получаем ID канала
    conn = sqlite3.connect('db_lectures', check_same_thread=False)  # Подключаемся к базе данных лекций
    cursor = conn.cursor()  # Создаем курсор для выполнения SQL-запросов
    while True:
        # Извлекаем первую лекцию с неопубликованным статусом
        lecture = cursor.execute('SELECT * FROM lectures WHERE publication_status != ?', (1,)).fetchone()
        if lecture:  # Если лекция найдена
            video_path = lecture[2].split(":")[0]  # Получаем путь к видео
            audio_path = f"{lecture[2].split(':')[1]}.mp3"  # Получаем путь к аудио
            mess = f"{lecture[4]}\n#{lecture[3]} #{lecture[5]}"  # Формируем сообщение с информацией о лекции

            with open(video_path, "rb") as video:  # Открываем видеофайл
                bot.send_video(CHANNEL_ID, video, caption=mess, timeout=300)  # Отправляем видео в канал

            with open(audio_path, "rb") as audio:  # Открываем аудиофайл
                bot.send_audio(CHANNEL_ID, audio, caption="Аудиоверсия лекции", timeout=300)  # Отправляем аудио в канал

            # Обновляем статус лекции в базе данных
            cursor.execute('UPDATE lectures SET publication_status = ? WHERE publication_status != ?', (1, 1))
            conn.commit()  # Сохраняем изменения
        time.sleep(5)  # Задержка перед следующей проверкой


# Обработчик команды /study_buddy
@bot.message_handler(commands=['study_buddy'])
def activate_study_buddy(message):
    """
    Активирует режим "учебного помощника".
    """
    global study_buddy_mode  # Объявляем глобальную переменную для режима помощника
    user_id = message.chat.id  # Получаем ID пользователя
    study_buddy_mode[user_id] = True  # Устанавливаем режим помощника для пользователя
    bot.send_message(message.chat.id,
                     "Передайте мне видео и по возможности некоторую дополнительную информацию.")  # Запрашиваем видео и информацию


# Обработчик сообщений в режиме "учебного помощника"
@bot.message_handler(func=lambda message: study_buddy_mode.get(message.chat.id, False))
def handle_message(message):
    """
    Обрабатывает сообщения, когда активирован режим "учебного помощника".
    """
    global study_buddy_mode  # Объявляем глобальную переменную
    text = message.text  # Получаем текст сообщения

    # Шаблон для поиска ссылки
    URL_PATTERN = r"(https?://[^\s]+)"  # Регулярное выражение для поиска ссылок
    link_match = re.search(URL_PATTERN, text)  # Поиск ссылки в тексте

    if link_match:  # Если ссылка найдена
        # Обрабатываем её
        link = link_match.group(0)  # Извлекаем найденную ссылку
        description = text.replace(link, "").strip()  # Извлекаем описание, удаляя ссылку

        # Создаем поток для загрузки данных с Яндекс.Диска
        refresh_thread = threading.Thread(target=download_from_yandex_disk, args=(link, description))
        refresh_thread.daemon = True  # Завершит поток при завершении основного потока
        refresh_thread.start()  # Запускаем поток

        bot.reply_to(message,
                     "Ссылка и описание получены! После обработки запись будет опубликована в канале.")  # Подтверждение получения
        bot.send_message(message.chat.id, config.HELP_INFORMATION)  # Отправляем информацию о помощи
        # Выключаем режим после успешного получения ссылки
        study_buddy_mode[message.chat.id] = False  # Отключаем режим помощника
    else:
        # Если ссылка не найдена, уведомляем пользователя
        bot.reply_to(message,
                     "Не могу найти ссылку в сообщении. Пожалуйста, проверьте его формат.")  # Сообщаем о неверном формате сообщения


# Функция для отправки вопроса и ожидания ответа
def ask_question(message, questions, question_index, score):
    if question_index < len(questions):
        q = questions[question_index]
        bot.send_message(message.chat.id, q["question"], reply_markup=generate_command_keyboard())
        for option in q["options"]:
            bot.send_message(message.chat.id, option)

        # Регистрируем обработчик ответа
        @bot.message_handler(content_types=['text'])
        def handle_answer(message):
            # Получаем ответ пользователя
            answer = message.text.lower()
            if answer == "5":
                bot.send_message(message.chat.id, f"Тест остановлен")
                return
            # Обновляем счет в зависимости от ответа
            if answer in q["scores"]:
                for hobby in q["scores"][answer]:
                    score[hobby] += 1

            # Переходим к следующему вопросу
            time.sleep(1)
            ask_question(message, questions, question_index + 1, score)

        bot.register_next_step_handler(message, handle_answer)

    else:
        # Определение наиболее подходящего увлечения
        max_score = max(score.values())
        best_hobbies = [hobby for hobby, s in score.items() if s == max_score]

        bot.send_message(message.chat.id, "Ваши результаты:")
        for hobby in best_hobbies:
            bot.send_message(message.chat.id, f"- {hobby}")


class TourState:
    start_location = "start_location"
    confirm_location = "confirm_location"
    next_location = "next_location"


@bot.message_handler(commands=['activities'])
def activities(message):
    bot.send_message(message.chat.id, ("Пройдите тест, чтобы определить, какое увлечение вам больше подходит!"))
    bot.send_message(message.chat.id, ("Ответьте на следующие вопросы, выбрав номер подходящего варианта.n"))

    score = {
        "Объединенный совет обучающихся ЗабГУ": 0,
        "Ассоциация волонтерских отрядов": 0,
        "Студенческие педагогические отряды": 0,
        "Студенческие строительные отряды": 0,
        "Студенческие отряды проводников поезда": 0,
        "Музыкальный коллектив": 0,
        "Клуб веселых и находчивых (КВН)": 0,
        "Театральный коллектив": 0,
        "Спортивный клуб": 0
    }

    questions = [
        {
            "question": "1. Как вы предпочитаете проводить свободное время?",
            "options": [
                "1) Помогать другим и участвовать в социальных проектах.",
                "2) Заниматься творчеством и искусством.",
                "3) Участвовать в спортивных мероприятиях.",
                "4) Работать в команде над проектами.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Ассоциация волонтерских отрядов", "Объединенный совет обучающихся ЗабГУ"],
                '2': ["Музыкальный коллектив", "Театральный коллектив", "Клуб веселых и находчивых (КВН)"],
                '3': ["Спортивный клуб"],
                '4': ["Студенческие педагогические отряды", "Студенческие строительные отряды",
                      "Студенческие отряды проводников поезда"]
            }
        },
        {
            "question": "2. Какой тип деятельности вам ближе?",
            "options": [
                "1) Организация мероприятий и помощь другим.",
                "2) Творческое самовыражение.",
                "3) Спортивные достижения.",
                "4) Работа в команде над общими целями.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Объединенный совет обучающихся ЗабГУ", "Ассоциация волонтерских отрядов"],
                '2': ["Музыкальный коллектив", "Театральный коллектив", "Клуб веселых и находчивых (КВН)"],
                '3': ["Спортивный клуб"],
                '4': ["Студенческие педагогические отряды", "Студенческие строительные отряды",
                      "Студенческие отряды проводников поезда"]
            }
        },
        {
            "question": "3. Как вы относитесь к работе в команде?",
            "options": [
                "1) Мне это нравится, я люблю работать с людьми.",
                "2) Я предпочитаю работать самостоятельно.",
                "3) Я могу работать в команде, если есть четкая цель.",
                "4) Я люблю быть лидером команды.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Ассоциация волонтерских отрядов", "Объединенный совет обучающихся ЗабГУ"],
                '2': ["Музыкальный коллектив", "Театральный коллектив"],
                '3': ["Студенческие педагогические отряды", "Спортивный клуб"],
                '4': ["Студенческие строительные отряды", "Клуб веселых и находчивых (КВН)"]
            }
        },
        {
            "question": "4. Какой вид искусства вам ближе?",
            "options": [
                "1) Музыка.",
                "2) Театр.",
                "3) Изобразительное искусство.",
                "4) Литература.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Музыкальный коллектив"],
                '2': ["Театральный коллектив"],
                '3': ["Клуб веселых и находчивых (КВН)"],
                '4': ["Объединенный совет обучающихся ЗабГУ"]
            }
        },
        {
            "question": "5. Как вы относитесь к спорту?",
            "options": [
                "1) Я занимаюсь спортом регулярно.",
                "2) Я предпочитаю смотреть спорт по телевизору.",
                "3) Спорт — это не для меня.",
                "4) Я люблю участвовать в спортивных мероприятиях.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Спортивный клуб"],
                '2': ["Ассоциация волонтерских отрядов"],
                '3': ["Объединенный совет обучающихся ЗабГУ"],
                '4': ["Студенческие педагогические отряды"]
            }
        },
        {
            "question": "6. Что вас вдохновляет?",
            "options": [
                "1) Успехи других людей.",
                "2) Природа и окружающий мир.",
                "3) Литература и искусство.",
                "4) Спортивные достижения.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Объединенный совет обучающихся ЗабГУ"],
                '2': ["Ассоциация волонтерских отрядов"],
                '3': ["Музыкальный коллектив", "Театральный коллектив"],
                '4': ["Спортивный клуб"]
            }
        },
        {
            "question": "7. Выберите занятие, которое вам интересно:",
            "options": [
                "1) Волонтерство и помощь нуждающимся.",
                "2) Участие в театральных постановках.",
                "3) Спортивные тренировки и соревнования.",
                "4) Организация мероприятий.",
                "5) Отменить опрос"
            ],
            "scores": {
                '1': ["Ассоциация волонтерских отрядов"],
                '2': ["Театральный коллектив"],
                '3': ["Спортивный клуб"],
                '4': ["Объединенный совет обучающихся ЗабГУ"]
            }
        },
    ]

    # Запускаем тест
    ask_question(message, questions, 0, score)


# Запускаем поток для мониторинга новых лекций
flag_monitor_thread = threading.Thread(target=monitor_flag)
flag_monitor_thread.daemon = True  # Завершит поток при завершении основного потока
flag_monitor_thread.start()

bot.polling(none_stop=True)

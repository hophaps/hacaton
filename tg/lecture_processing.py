import requests  # Библиотека для работы с HTTP-запросами
import uuid  # Библиотека для генерации уникальных идентификаторов
import time  # Библиотека для работы с временем
import threading  # Библиотека для работы с потоками
import os  # Библиотека для работы с операционной системой
from dotenv import load_dotenv  # Библиотека для загрузки переменных окружения из .env файла
from moviepy.editor import *  # Библиотека для редактирования видео
import json  # Библиотека для работы с JSON
import sqlite3  # Библиотека для работы с SQLite базами данных
from datetime import datetime  # Библиотека для работы с датой и временем
from urllib.parse import urlparse, parse_qs  # Библиотека для разбора URL

# Загрузим переменные из текущего .env файла
load_dotenv()

# Подключение к базе данных SQLite с флагом для поддержки многопоточности
conn = sqlite3.connect('db_lectures', check_same_thread=False)
cursor = conn.cursor()

def add_lecture(name, lecturer="", retelling="", discipline="", link=""):
    # Функция для добавления лекции в базу данных
    current_date = datetime.now().strftime("%Y-%m-%d")  # Получаем текущую дату в формате "YYYY-MM-DD"
    cursor.execute('''INSERT INTO lectures (date, name, lecturer, retelling, discipline, link)
                        VALUES (?, ?, ?, ?, ?, ?)''', (current_date, name, lecturer, retelling, discipline, link))
    conn.commit()  # Сохраняем изменения в базе данных
    conn.close()  # Закрываем соединение с базой данных

def refresh_token_saluteSpeech():
    # Функция для периодического обновления токена доступа к API SaluteSpeech
    while True:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"  # URL для запроса токена
        headers = {
            "Authorization": f"Basic {os.getenv('SALUTESPEECH_AUTHORIZATION')}",  # Заголовок авторизации
            "RqUID": str(uuid.uuid4()),  # Генерация уникального идентификатора запроса
            "Content-Type": "application/x-www-form-urlencoded"  # Указываем тип контента
        }

        # Параметры для тела запроса
        data = {
            "scope": "SALUTE_SPEECH_PERS"  # Указываем область для получения токена
        }

        # Отправка POST-запроса
        response = requests.post(url, headers=headers, data=data, verify=False)

        # Обработка ответа
        if response.ok:  # Если запрос успешен
            data = response.json()  # Парсим JSON из ответа
            ACCESS_TOKEN = data.get("access_token")  # Получаем токен доступа

            # Добавление или обновление переменной в .env файле
            with open(".env", "r") as file:
                lines = file.readlines()

            for i, line in enumerate(lines):
                if line.startswith("SALUTESPEECH_ACCESS_TOKEN="):  # Находим строку с токеном
                    lines[i] = f"SALUTESPEECH_ACCESS_TOKEN={ACCESS_TOKEN}\n"  # Обновляем токен

            # Перезаписываем файл с новыми данными
            with open(".env", "w") as file:
                file.writelines(lines)

            load_dotenv(override=True)  # Перезагружаем переменные окружения
        else:
            print("Ошибка:", response.status_code, response.text)  # Логируем ошибку
        time.sleep(25 * 60)  # Ожидание 25 минут

def refresh_token_gigachat():
    # Функция для периодического обновления токена доступа к API GigaChat
    while True:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        payload = 'scope=GIGACHAT_API_PERS'  # Параметры запроса
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),  # Генерация уникального идентификатора запроса
            'Authorization': f'Basic {os.getenv("GIGACHAT_AUTHORIZATION")}'  # Заголовок авторизации
        }

        response = requests.request("POST", url, headers=headers, data=payload, verify=False)  # Отправка POST-запроса
        if response.ok:  # Если запрос успешен
            data = response.json()  # Парсим JSON из ответа
            ACCESS_TOKEN = data.get("access_token")  # Получаем токен доступа

            # Добавление или обновление переменной в .env файле
            with open(".env", "r") as file:
                lines = file.readlines()

            for i, line in enumerate(lines):
                if line.startswith("GIGACHAT_ACCESS_TOKEN="):  # Находим строку с токеном
                    lines[i] = f"GIGACHAT_ACCESS_TOKEN={ACCESS_TOKEN}\n"  # Обновляем токен

            # Перезаписываем файл с новыми данными
            with open(".env", "w") as file:
                file.writelines(lines)

            load_dotenv(override=True)  # Перезагружаем переменные окружения
        else:
            print("Ошибка:", response.status_code, response.text)  # Логируем ошибку
        time.sleep(25 * 60)  # Ожидание 25 минут

def abbreviation_of_text(video_path, audio_path, text, description, public_url):
    # Функция для создания аббревиатуры текста с помощью GigaChat
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",  # Указываем модель для работы
        "messages": [
            {
                "role": "user",
                "content": f"""Сделай конспект по этой лекции: 
                {text}"""  # Текст для конспекта
            }
        ],
        "stream": False,  # Указываем, что не используем стриминг
        "repetition_penalty": 1  # Штраф за повторение
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {os.getenv("GIGACHAT_ACCESS_TOKEN")}'  # Заголовок авторизации
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)  # Отправка POST-запроса
    response_data = response.json()
    content = response_data.get("choices")[0].get("message").get("content")  # Извлекаем содержание конспекта
    supporting_information = description.split("\n")  # Разбиваем описание на строки

    # Добавляем лекцию в базу данных
    add_lecture(f"{video_path}:{audio_path}", retelling=content, lecturer=supporting_information[0], discipline=supporting_information[1], link=public_url)

def send_audio_to_api(video_path, description, public_url):
    # Функция для извлечения аудио из видео и отправки его на API
    video = VideoFileClip(video_path)  # Открываем видеофайл
    audio_path = video_path.split(".")[0]  # Создаем путь для сохранения аудио
    video.audio.write_audiofile(f"{audio_path}.mp3")  # Сохраняем аудио в формате MP3

    # Работа с API
    url = "https://smartspeech.sber.ru/rest/v1/data:upload"
    headers = {
        "Authorization": f"Bearer {os.getenv('SALUTESPEECH_ACCESS_TOKEN')}"  # Заголовок авторизации
    }

    with open(f"{audio_path}.mp3", "rb") as audio_buffer:
        # Отправляем POST-запрос с аудиобуфером
        response = requests.post(url, headers=headers, data=audio_buffer, verify=False)

    if response.ok:  # Если запрос успешен
        response_data = response.json()
        file_id = response_data.get("result", {}).get("request_file_id")  # Получаем ID загруженного файла
        url = "https://smartspeech.sber.ru/rest/v1/speech:async_recognize"  # URL для распознавания речи
        headers = {
            "Authorization": f"Bearer {os.getenv('SALUTESPEECH_ACCESS_TOKEN')}",  # Заголовок авторизации
            "Content-Type": "application/json"  # Указываем тип контента
        }

        data = {
            "options": {
                "language": "ru-RU",  # Указываем язык
                "audio_encoding": "MP3",  # Указываем формат аудио
                "hypotheses_count": 1,  # Количество гипотез
                "enable_profanity_filter": False,  # Отключаем фильтр ненормативной лексики
                "max_speech_timeout": "20s",  # Максимальное время ожидания речи
                "channels_count": 2,  # Количество каналов
                "no_speech_timeout": "7s",  # Время ожидания безречной активности
                "speaker_separation_options": {
                    "enable": True,  # Включаем разделение говорящих
                    "enable_only_main_speaker": True,  # Включаем только основного говорящего
                    "count": 2  # Количество говорящих
                }
            },
            "request_file_id": file_id  # ID загруженного файла
        }

        # Запрос на распознавание речи
        response = requests.post(url, headers=headers, json=data, verify=False)

        if response.status_code == 200:  # Если запрос успешен
            response_data = response.json()
            id_task = response_data.get("result", {}).get("id")  # Получаем ID задачи
            url = "https://smartspeech.sber.ru/rest/v1/task:get"  # URL для получения статуса задачи
            headers = {
                "Authorization": f"Bearer {os.getenv('SALUTESPEECH_ACCESS_TOKEN')}"  # Заголовок авторизации
            }

            params = {
                "id": id_task  # Параметры с ID задачи
            }

            response = requests.get(url, headers=headers, params=params, verify=False)  # Запрос на получение статуса задачи

            if response.status_code == 200:  # Если запрос успешен
                response_json = response.json()
                status = response_json.get("result", {}).get("status")  # Получаем статус задачи
                print(status)
                response_file_id = response_json.get("result", {}).get("response_file_id")  # Получаем ID ответа
                while status != "DONE":  # Ожидаем завершения задачи
                    time.sleep(30)  # Ждем 30 секунд
                    response = requests.get(url, headers=headers, params=params, verify=False)  # Проверяем статус задачи
                    response_json = response.json()
                    status = response_json.get("result", {}).get("status")
                    print(status)  # Логируем статус
                    response_file_id = response_json.get("result", {}).get("response_file_id")

                # Загружаем файл с распознанным текстом
                url = "https://smartspeech.sber.ru/rest/v1/data:download"
                headers = {
                    "Authorization": f"Bearer {os.getenv('SALUTESPEECH_ACCESS_TOKEN')}"  # Заголовок авторизации
                }

                params = {
                    "response_file_id": response_file_id  # Параметры с ID ответа
                }

                response = requests.get(url, headers=headers, params=params, stream=True, verify=False)  # Запрос на загрузку

                if response.status_code == 200:  # Если запрос успешен
                    data = response.json()
                    text = ""
                    for index, i in enumerate(data):
                        if index % 2 == 0:  # Проверяем, является ли индекс четным
                            if "results" in i and len(i["results"]) > 0:
                                text += f'{i["results"][0]["normalized_text"]} '  # Собираем текст
                    print("File downloaded successfully.")  # Успешно загружен
                    abbreviation_of_text(video_path, audio_path, text, description, public_url)  # Создаем аббревиатуру текста
                else:
                    print("Ошибка:", response.status_code, response.text)  # Логируем ошибку

            else:
                print("Ошибка:", response.status_code, response.text)  # Логируем ошибку
        else:
            print("Ошибка:", response.status_code, response.text)  # Логируем ошибку

def download_from_yandex_disk(public_url, description):
    # Функция для загрузки файла из Яндекс.Диска
    download_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'  # URL для получения прямой ссылки
    params = {'public_key': public_url}  # Параметры запроса

    # Получение прямой ссылки для скачивания и информации о файле
    response = requests.get(download_url, params=params)
    response_json = response.json()

    # Получение ссылки для скачивания и имени файла
    download_link = response_json.get('href')  # Ссылка для скачивания
    parsed_url = urlparse(download_link)  # Разбор URL
    query_params = parse_qs(parsed_url.query)  # Получение параметров запроса
    filename = query_params.get('filename', ['unknown'])[0]  # Извлекаем имя файла

    # Проверяем, что ссылка на скачивание и имя файла получены успешно
    if download_link and filename:
        # Скачивание файла
        file_response = requests.get(download_link)
        with open(f"data/media/{filename}", 'wb') as file:
            file.write(file_response.content)  # Записываем содержимое файла
        print(f"Файл '{filename}' успешно скачан.")  # Успешно скачан
        send_audio_to_api(f"data/media/{filename}", description, public_url)  # Отправляем аудио на API
    else:
        print("Не удалось получить ссылку или имя файла для скачивания.")  # Логируем ошибку

# Запускаем потоки для обновления токена
refresh_thread = threading.Thread(target=refresh_token_saluteSpeech)  # Создаем поток для обновления токена SaluteSpeech
refresh_thread.daemon = True  # Завершит поток при завершении основного потока
refresh_thread.start()  # Запускаем поток

sta_thread = threading.Thread(target=refresh_token_gigachat)  # Создаем поток для обновления токена GigaChat
sta_thread.daemon = True  # Завершит поток при завершении основного потока
sta_thread.start()  # Запускаем поток
time.sleep(5)  # Задержка на 5 секунд перед дальнейшими действиями

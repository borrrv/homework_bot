"""
This program create from YP for me.

Author: Boroday Vladislav
Date: 30.09.2022
"""
from http import HTTPStatus
from logging import FileHandler, Formatter, getLogger, StreamHandler
from dotenv import load_dotenv

import settings
import os
import telegram
import requests
import logging
import time
import sys

load_dotenv()


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


logging.basicConfig(
    level=logging.DEBUG,
    filename='assistant.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

file = FileHandler('assistantYP.log')
logger = getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(sys.stdout)
formatter = Formatter('%(asctime)s, %(levelname)s, %(message)s, %(name)s')
logger.addHandler(handler)
logger.addHandler(file)
file.setFormatter(formatter)


def send_message(bot, message):
    """Message sent from bot."""
    logger.info('Start message sent')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                         text=message)
        logger.info('Message sent')
    except Exception:
        logger.error('Error message sent')


def get_api_answer(current_timestamp):
    """Request to API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=settings.ENDPOINT,
                                headers=HEADERS,
                                params=params)
        logger.info('Request to API')
    except Exception:
        logger.error('Network problem, please try again later')
    if response.status_code == HTTPStatus.OK:
        status_code = response.status_code
        try:
            response = response.json()
            return response
        except Exception:
            logger.error('Unidentified format, json expected')
    else:
        raise Exception(f'Error {status_code}')


def check_response(response):
    """Verification the API for correctness."""
    if not isinstance(response, dict):
        raise TypeError('API is not dict')
    try:
        response_hw = response['homeworks']
        if isinstance(response_hw, list) is False:
            raise TypeError('Homeworks are not list')
    except Exception:
        raise KeyError("No key 'homeworks'")
    try:
        homework = response_hw[0]
    except Exception:
        raise IndexError('Reviewer did not start the check')
    return homework


def parse_status(homework):
    """
    Status homework.

    Extracting the status of this work from information
    about a particular homework.
    """
    if 'homework_name' not in homework:
        raise KeyError('This key is not valid')
    if 'status' not in homework:
        raise Exception('This key is not valid')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status in settings.HOMEWORK_STATUSES:
        verdict = settings.HOMEWORK_STATUSES[homework_status]
        logger.info('Check status changed')
        tex = f"Изменился статус проверки работы \"{homework_name}\".{verdict}"
        return tex


def check_tokens():
    """Verification environment variable."""
    if (TELEGRAM_TOKEN is None
        and PRACTICUM_TOKEN is None
            and TELEGRAM_CHAT_ID is None):
        logger.critical('Environment variables not found')
        return False
    else:
        return True


def main():
    """General logic of work."""
    old_version_message = None
    if not check_tokens():
        raise Exception('Environment variable not found')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                homework_status = parse_status(homework)
                if homework_status != old_version_message:
                    message = old_version_message
                    send_message(bot, message)
                logger.info(
                    'Update not found, please check after 10 minutes'
                )
                time.sleep(settings.RETRY_TIME)

        except Exception as error:
            message = f'{error}'
            logger.error(message)
            send_message(bot, message)
        time.sleep(settings.RETRY_TIME)


if __name__ == '__main__':
    main()

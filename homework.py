from http import HTTPStatus
from logging.handlers import RotatingFileHandler
import sys
from xmlrpc.client import ResponseError
import telegram
import time
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(stream=sys.stdout)],
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)


def send_message(bot, message):
    '''Отправка сообщения'''
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except Exception:
        logger.error('Сбой отправки сообщение')


def get_api_answer(current_timestamp):
    '''Отправка запроса к API'''
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        logger.error('Сбой при отправке запроса')
    if response.status_code != HTTPStatus.OK:
        logger.error('Код ответа сервера не ОК')
        raise Exception('Код ответа сервера не ОК')
    return response.json()


def check_response(response):
    '''Проверка ответа'''
    if not isinstance(response, dict):
        logging.error('Ответ не является словарем')
        raise TypeError('Ответ не в виде словаря')
    if ('homeworks' or 'current_date') not in response:
        logging.error('Ответ API некорректный')
        raise ResponseError('В ответе отсутствуют домашние работы')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logging.error('Домашние работы не в виде списка')
        raise TypeError('Домашние работы не в виде списка')
    logging.info('Ответ API корректный')
    return homeworks


def parse_status(homework):
    '''Измениние статуса'''
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    '''Проверка токенов'''
    if TELEGRAM_TOKEN is None:
        logger.critical('Отствует логин телеграмм')
        return False
    if PRACTICUM_TOKEN is None:
        logger.critical('Отсутсвует логин Яндекса')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        return check_tokens()
    else:
        logger.info('Проверка токенов прошла успешно')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

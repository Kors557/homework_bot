from logging.handlers import RotatingFileHandler
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
    filename='program.log',
    filemode='a',
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
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except Exception:
        logger.error('Сбой отправки сообщение')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        logger.error('Сбой при отправке запроса')
    return response.json()


def check_response(response):
    try:
        homework_list = response['homeworks']
    except Exception:
        if len(homework_list) == 0:
            logger.error('Список пуст')
    return homework_list


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('homework_status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
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
            current_timestamp = current_timestamp
            time.sleep(RETRY_TIME)
            message = parse_status(homework[0])
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            time.sleep(RETRY_TIME)
        else:
            logger.error('Что то не работает')


if __name__ == '__main__':
    main()

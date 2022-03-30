class WrongAPIResponseCodeError(Exception):
    """Ошибка ответа API."""
    pass


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""
    pass


class TokinError(Exception):
    """Отстутсвует токен!"""
    pass

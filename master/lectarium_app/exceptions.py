class CustomException(Exception):
    pass


class StatusChangeError(CustomException):
    """
    Выбрасывается при ошибках смены статуса
    """


class ClmOperationalError(CustomException):
    """
    Выбрасывается при ошибках во время обращения к ClickMeeting API
    """

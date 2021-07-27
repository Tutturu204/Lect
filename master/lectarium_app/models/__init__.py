from datetime import datetime, date

from .. import db
from lectarium_app.models.webinar_entities import Webinar


def str_now():
    return datetime.now().strftime("%F %T")


def str_today():
    return date.today().strftime("%F")


def parse_date(iso_str):
    if isinstance(iso_str, str):
        return datetime.strptime(iso_str, '%Y-%m-%d').date()
    elif isinstance(iso_str, date):
        return iso_str
    raise TypeError('Cannot parse date from {}'.format(iso_str))


# Создание всех таблиц, упоминающихся в модулях
db.create_all()
db.session.commit()

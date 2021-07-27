from lectarium_app import session, clm_service, logger, executor
from lectarium_app.models.webinar_entities import Webinar, WebinarToken
from lectarium_app.exceptions import StatusChangeError, ClmOperationalError
from datetime import datetime, timedelta


def get_web(webinar_id):
    return Webinar.query.get_or_404(webinar_id)


def update_web_status(webinar_id, status):
    all_possible_statuses = {"CREATED": ["PLANNED"],
                             "PLANNED": ["BEGINNING"],
                             "BEGINNING": ["IN_PROGRESS"],
                             "IN_PROGRESS": ["FINISHED"],
                             "FINISHED": ["UPLOADED"],
                             "UPLOADED": ["AVAILABLE"],
                             "AVAILABLE": ["UPLOADED"]
                             }
    current_web = get_web(webinar_id)
    previous_status = current_web.status
    if status in all_possible_statuses[previous_status]:
        current_web.status = status
        session.add(current_web)
        session.commit()
        return current_web
    else:
        raise StatusChangeError(previous_status, status)


def get_all_webs_by_status(status):
    return Webinar.query.filter_by(status).all()


def get_webinar(webinar_id):
    return Webinar.query.get_or_404(webinar_id)


@executor.job
def create_or_update_webinars_tokens(webinar_id):
    logger.info('Creating wtokens')
    try:
        webinar = Webinar.query.get_or_404(webinar_id)
        status, tokens = clm_service.generate_and_get_tokens(webinar.room_id, webinar.cm_account_login,
                                                             webinar.cm_account.userplan * 4)
        if status['new']:
            for token in tokens:
                session.add(WebinarToken(webinar=webinar, user=None, token=token))
        else:
            for token in tokens:
                if not WebinarToken.query.filter(WebinarToken.token == token).one_or_none():
                    session.add(WebinarToken(webinar=webinar, user=None, token=token))

        session.commit()
    except Exception as e:
        logger.error('Error while generating wtokens: %s', e)
    else:
        logger.info('Creating wtokens completed')


# Округление времени до целых минут
def round_to_minutes(date_time):
    date_hrs, mins, _ = date_time.split(':')
    return ':'.join([date_hrs, mins, '00'])


def create_webinar(initiator, data):
    data['start_date'] = round_to_minutes(data['start_date'])
    if data['webinar_type'] == 'MANUALLY_UPLOADED':
        data['status'] = 'UPLOADED'
        data['begin_date'] = None
        data['created_at'] = None
        # TODO: data['duration'] = get_duration_from_vimeo(data['vimeo_id'])
    else:
        if data['webinar_type'] == 'CLICKMEETING':
            response = clm_service.post_conference(data)

            hrs, mins = map(int, data['duration'].split(':'))
            data['duration'] = timedelta(hours=hrs, minutes=mins)
            data['room_id'] = response['room']['id']
            data['webinar_link'] = response['room']['room_url']
        data['created_at'] = datetime.now()
        data['status'] = 'PLANNED'
    data['initiator_lect_id'] = initiator.lect_id
    webinar = Webinar(**data)
    session.add(webinar)
    session.commit()
    # We need webinar in database to create WebinarToken item
    create_or_update_webinars_tokens.submit(webinar.webinar_id)
    return webinar


def update_webinar(webinar_id, data):
    webinar = get_webinar(webinar_id)

    attrs = [column.name for column in Webinar.__table__.columns]
    for attr in attrs:
        if attr in data:
            setattr(webinar, attr, data[attr])

    session.add(webinar)
    session.commit()
    return webinar


def delete_webinar(webinar_id):
    webinar = get_webinar(webinar_id)
    clm_service.delete_conference(webinar.room_id, webinar.cm_account_login)
    session.delete(webinar)
    session.commit()


def send_notification_about_beginning(webinar_id):
    pass


def is_webinar_finished_in_clm(webinar_id):
    webinar = get_web(webinar_id)
    if datetime.now() > webinar.end_date:
        return True
    else:
        return False


def is_in_past(date_time):
    if isinstance(date_time, str):
        format = '%Y-%m-%dT%H:%M:%S'
        date_time = datetime.strptime(date_time, format)
    return date_time < datetime.today() + timedelta(minutes=5)


def validate_webinar_post(post_type, data):
    if post_type == 'planned':
        if data['webinar_type'] == 'CLICKMEETING':
            if not data.get('duration') or not data.get('cm_account_login'):
                return False, 'Duration or cm_account_login not specified'
        elif data['webinar_type'] == 'YOUTUBE':
            if not data.get('webinar_link'):
                return False, 'Webinar_link not specified'
        if data.get('duration'):
            try:
                hrs, mins = map(int, data['duration'].split(':'))
            except (ValueError, TypeError):
                return False, 'Incorrect duration format: {}'.format(data['duration'])
        if is_in_past(data['begin_date']):
            return False, 'Begin_date is in past'
    elif post_type == 'uploaded':
        pass
    else:
        return False, 'Wrong webinar post type "{}"'.format(post_type)
    return True, ''


def validate_webinar_delete(webinar_id):
    webinar = get_webinar(webinar_id)
    if webinar.status not in ['PLANNED']:
        return False, 'Can not delete webinar with status {}'.format(webinar.status)
    return True, ''


def validate_webinar_patch(webinar_id, data):
    webinar = get_webinar(webinar_id)
    if webinar.status == 'PLANNED':
        allowed_fields = ['name', 'description', 'preview_url', 'message_for_students',
                          'subjects', 'courses', 'products']
    elif webinar.status == 'UPLOADED':
        allowed_fields = ['name', 'description', 'preview_url', 'upload_date', 'vimeo_id',
                          'subjects', 'courses', 'products']
    else:
        return False, 'Can not edit webinar with status {}'.format(webinar.status)

    for field in data:
        if field not in allowed_fields:
            return False, 'Editing field {} is forbidden for webinar with status {}'.format(field, webinar.status)
    return True, ''

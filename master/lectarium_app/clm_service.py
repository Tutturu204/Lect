import urllib.error
import urllib.parse
import urllib.request

import datetime

import json
import requests

from lectarium_app.exceptions import ClmOperationalError
from lectarium_app import webinar_service
from lectarium_app import logger

cm_url = 'https://api.clickmeeting.com/v1'


# TODO: perhaps, move to separate file if reused
def build_query(params):
    def build_query_item(params, base_key=None):
        results = list()

        if type(params) is dict:
            for key, value in list(params.items()):
                if base_key:
                    new_base = urllib.parse.quote("{0}[{1}]".format(base_key, key))
                    results += build_query_item(value, new_base)
                else:
                    results += build_query_item(value, key)
        elif type(params) is list:
            for index, value in enumerate(params):
                if base_key:
                    results += build_query_item(value, "{0}[]".format(base_key))
                else:
                    results += build_query_item(value)
        else:
            if params is not None:
                quoted_item = urllib.parse.quote(str(params))
                if base_key:
                    results.append("{0}={1}".format(base_key, quoted_item))
                else:
                    results.append(quoted_item)
        return results

    return '&'.join(build_query_item(params))


def send_request(cm_login, method, path, params=None):
    response = requests.request(method=method.upper(),
                                url='{0}{1}.json'.format(cm_url, path),
                                headers={
                                    'X-Api-Key': clm_service.get_cm_account(cm_login).api_key,
                                    'Content-Type': 'application/x-www-form-urlencoded'
                                },
                                data=build_query(params),
                                verify=True
                                )
    if not response.ok:
        raise ClmOperationalError(response.content)

    return response.json()


def generate_and_get_tokens(room_id, cm_account_login, how_many):
    """
    :return: status, tokens
    status:   { 'new':
                True - all tokens are new
                False - some tokens are not new
                'enough':
                True - exactly how_many tokens were generated
                False - less than how_many tokens were generated
    tokens:   list of clm tokens
    """
    status = {'new': True, 'enough': True}
    try:
        response = send_request(cm_account_login, 'POST', '/conferences/' + str(room_id) + '/tokens',
                                {'how_many': how_many})
        return status, [token_item['token'] for token_item in response['access_tokens']]

    except ClmOperationalError as e:
        # If response is 403: FORBIDDEN, probably some tokens were already generated
        try:
            response = json.loads(e.args[0])
            message = response['errors'][0]['message'].strip().split(' ')
            generated, allowed = int(message[8]), int(message[17])
        except:
            raise ClmOperationalError(e.args[0])

        # Update userplan if necessary
        status['new'] = False
        cm_account = clm_service.get_cm_account(cm_account_login)
        if cm_account.userplan * 4 != allowed:
            clm_service.update_cm_account(cm_account_login, userplan=allowed // 4)
            logger.info('Updated userplan for {} to {} viewers'.format(cm_account_login, allowed // 4))

        # Generate as many tokens as possible
        if allowed > generated:
            send_request(cm_account_login, 'POST', '/conferences/' + str(room_id) + '/tokens',
                         {'how_many': allowed - generated})

        # Return generated tokens
        response = send_request(cm_account_login, 'GET', '/conferences/' + str(room_id) + '/tokens',
                                {'how_many': how_many})
        if allowed >= how_many:
            return status, [token_item['token'] for token_item in response['access_tokens'][-(allowed - how_many):]]
        else:
            status['enough'] = False
            return status, [token_item['token'] for token_item in response['access_tokens']]


def get_autologin_hash(lect_user, webinar, token):
    params = {
        'email': lect_user.email if lect_user.email else 'User' + str(lect_user.lect_id) + '@lectarium.ru',
        'nickname': lect_user.profile.first_name if lect_user.profile.first_name else 'Студент ' + str(
            lect_user.lect_id),
        'role': 'listener',
        'token': token
    }

    response = send_request(webinar.cm_account_login, 'POST',
                            '/conferences/' + str(webinar.room_id) + '/room/autologin_hash', params)
    return response['autologin_hash']


# Костыль для вычитания 3 часов из времени
def transform_datetime(date_time):
    format = '%Y-%m-%dT%H:%M:%S'
    return (datetime.datetime.strptime(date_time, format) - datetime.timedelta(hours=3)).strftime(format)


def post_conference(data):
    params = {
        'name': data['name'],
        'room_type': 'webinar',
        'permanent_room': 0,
        'access_type': 3 if data['is_closed'] else 1,
        'lobby_description': data['description'],
        'lobby_enabled': 1,
        'starts_at': transform_datetime(data['start_date']),
        'duration': data['duration'],
        'timezone': 'Europe/Moscow',
        # 'skin_id': 1,
        'registration ': {
            'enabled': 1,
            # 'template': 1
        },
        'settings': {
            'show_on_personal_page': 1,
            'thank_you_emails_enabled': 1,
            'connection_tester_enabled': 0,
            # 'phonegateway_enabled':,
            # 'recorder_autostart_enabled':,
            # 'room_invite_button_enabled':,
            # 'social_media_sharing_enabled':,
            # 'connection_status_enabled':,
            'thank_you_page_url': ""
        }
    }
    return send_request(data['cm_account_login'], 'POST', '/conferences', params)


def edit_conference(room_id, cm_account_login, data):
    params = dict()

    if 'name' in data:
        params['name'] = data['name']
    if 'description' in data:
        params['lobby_description'] = data['description']
    # ClickMeeting API not working correctly for start_date
    # if 'start_date' in data:
    #    params['starts_at'] = transform_datetime(data['start_date'])

    return send_request(cm_account_login, 'PUT', '/conferences/{0}'.format(room_id), params)


def delete_conference(room_id, cm_account_login):
    return send_request(cm_account_login, 'DELETE', '/conferences/{0}'.format(room_id), params={'room_id': room_id})

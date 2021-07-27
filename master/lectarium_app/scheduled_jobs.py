"""
Файл с определениями функций, отрабатывающих через определенные промежутки времени,
независимо от обращений пользователей по api.
"""
from datetime import datetime, timedelta, time
from time import sleep

from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound

from lectarium_app import webinar_service
from lectarium_app import scheduler, logger, session
from lectarium_app.models import Webinar


@scheduler.task('cron', id='webinars_status_change', minute=5, max_instances=1)
def webinar_status_change():

    webinars_with_status_created = webinar_service.get_all_webs_by_status("CREATED")
    webinars_with_status_planned = webinar_service.get_all_webs_by_status("PLANNED")
    webinars_with_status_beginning = webinar_service.get_all_webs_by_status("BEGINNING")
    webinars_with_status_in_progress = webinar_service.get_all_webs_by_status("IN_PROGRESS")

    for webinar in webinars_with_status_created:
        try:
            if datetime.now() - webinar.created_at > timedelta(minutes=5):
                webinar_service.create_webinar_in_clm(webinar.webinar_id)
                webinar_service.update_web_status(webinar.webinar_id, "PLANNED")
        except Exception as ex:
            logger.error('Error while creating webinar: %s', ex)

    for webinar in webinars_with_status_planned:
        if webinar.start_date - timedelta(minutes=5) < datetime.now() < webinar.start_date:
            webinar_service.send_notification_about_beginning(webinar.webinar_id)
            webinar_service.update_web_status(webinar.webinar_id, "BEGINNING")

    for webinar in webinars_with_status_beginning:
        if datetime.now() > webinar.start_date:
            webinar_service.update_web_status(webinar.webinar_id, "IN_PROGRESS")

    for webinar in webinars_with_status_in_progress:
        if webinar_service.is_webinar_finished_in_clm(webinar.webinar_id):
            webinar_service.update_web_status(webinar.webinar_id, "FINISHED")

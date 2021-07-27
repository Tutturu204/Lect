import inspect
from lectarium_app import session, logger
from sqlalchemy_utils.aggregates import manager
from sqlalchemy import asc

from lectarium_app.models import User, Activity, ReceiptPosition, OrderPosition, Receipt, Order


def update_all_aggregated_fields():
    """
    Updates all columns with @aggregated decorator
    :return: None
    """
    for cls in [ReceiptPosition, Receipt, OrderPosition, Order, Activity]:
        logger.info('Updating aggregates, depending on {}'.format(cls.__name__))
        objects = cls.query.all()
        manager.construct_aggregate_queries(session, ...)  # Второй параметр не используется
        session.commit()


# В будущем здесь могут появиться функции для обновления отдельных полей

def update_first_activity_group_id():
    query = (session.query(User, Activity.group_id).filter(
        User.first_activity_group_id.is_(None)
    ).join(Activity, Activity.lect_id == User.lect_id)
             .filter(Activity.group_id.isnot(None))
             .order_by(asc(Activity.datetime))
             )

    for user, group_id in query:
        user.first_activity_group_id = group_id

    session.commit()


def update_first_payment():
    query = (session.query(User, OrderPosition.group_id, Receipt.payed_at)
             .join(Order, Order.student_vk_id == User.vk_id)
             .join(OrderPosition, OrderPosition.order_id == Order.order_id)
             .join(Receipt, Receipt.order_id == Order.order_id)
             .filter(Receipt.payed_at)
             )

    for user, group_id, date in query:
        assert user in session
        if not user.first_payment_date or date < user.first_payment_date:
            user.first_payment_date = date

    session.commit()

    for user, group_id, date in query:
        assert user in session
        if date == user.first_payment_date:
            if user.first_payment_group_ids:
                if group_id not in user.first_payment_group_ids:
                    user.first_payment_group_ids['ids'].append(group_id)
            else:
                user.first_payment_group_ids = {'ids': [group_id]}

    session.commit()

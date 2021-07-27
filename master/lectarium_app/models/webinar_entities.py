from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.functions import now
from . import db, str_now
from datetime import datetime


class VimeoAccount(db.Model):
    __tablename__ = 'vimeo_accounts'

    login = db.Column(db.String(50, collation='utf8mb4_unicode_ci'), primary_key=True)
    token = db.Column(db.String(40, collation='utf8mb4_unicode_ci'), nullable=False)
    client_id = db.Column(db.String(40, collation='utf8mb4_unicode_ci'), nullable=False)
    client_secret = db.Column(db.String(128, collation='utf8mb4_unicode_ci'), nullable=False)
    status = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<VimeoAccount "{0.login}", status={0.status}>'.format(self)


class CmAccount(db.Model):
    __tablename__ = 'cm_accounts'

    login = db.Column(db.String(50, collation='utf8mb4_unicode_ci'), primary_key=True)
    api_key = db.Column(db.String(60, collation='utf8mb4_unicode_ci'), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    default_room_name = db.Column(db.String(80, collation='utf8mb4_unicode_ci'))
    userplan = db.Column(db.Integer, nullable=False, default=100)

    def __repr__(self):
        return '<CmAccount "{0.login}", status={0.status}, default_room_name={0.default_room_name}>'.format(self)


class Webinar(db.Model):
    __tablename__ = 'webinars_added'

    webinar_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, index=True)
    name = db.Column(db.String(100, collation='utf8mb4_unicode_ci'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=now())
    begin_date = db.Column(db.DateTime, server_default=now())
    upload_date = db.Column(db.Date)
    duration = db.Column(db.Interval)
    is_closed = db.Column(db.Boolean, nullable=False, server_default='0')
    initiator_lect_id = db.Column(db.Integer)
    webinar_type = db.Column(db.Enum('CLICKMEETING', 'YOUTUBE', 'MANUALLY_UPLOADED'))
    webinar_link = db.Column(db.String(120))
    total_attendees = db.Column(db.Integer)
    max_attendees = db.Column(db.Integer)
    preview_url = db.Column(db.String(120))
    vimeo_id = db.Column(db.Integer)
    cm_account_login = db.Column(db.String(50, collation='utf8mb4_unicode_ci'), db.ForeignKey('cm_accounts.login'))
    description = db.Column(db.Text(collation='utf8mb4_unicode_ci'))
    message_for_students = db.Column(db.Text(collation='utf8mb4_unicode_ci'))
    status = db.Column(db.Enum("CREATED", "PLANNED", "BEGINNING", "IN_PROGRESS", "FINISHED", "UPLOADED", "AVAILABLE"),
                       nullable=False)
    #notification_before_minutes = db.Column(db.Integer, server_default='5')

    cm_account = db.relationship('CmAccount')
    wtokens = db.relationship('WebinarToken', back_populates='webinar')

    @property
    def products(self):
        return [wp.product for wp in self.webinars_products]

    @property
    def subjects(self):
        return [ws.subject for ws in self.webinars_subjects]

    @property
    def courses(self):
        return [wc.course for wc in self.webinars_courses]

    def __repr__(self):
        return '<Webinar #{0.webinar_id}>'.format(self)


class WebinarProduct(db.model):
    __tablename__ = 'webinars_products'
    webinar_product_pair_id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars_added.webinar_id'))
    product = db.Column(db.String(collation='utf8mb4_unicode_ci'))

    webinar = db.relationship('Webinar', backref='webinars_products')


class WebinarSubject(db.model):
    __tablename__ = 'webinars_subjects'
    webinar_subject_pair_id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars_added.webinar_id'))
    subject = db.Column(db.String(collation='utf8mb4_unicode_ci'))

    webinar = db.relationship('Webinar', backref='webinars_subjects')


class WebinarCourse(db.model):
    __tablename__ = 'webinars_courses'
    webinar_course_pair_id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars_added.webinar_id'))
    course = db.Column(db.String(collation='utf8mb4_unicode_ci'))

    webinar = db.relationship('Webinar', backref='webinars_courses')


class WebinarToken(db.Model):
    __tablename__ = 'webinars_tokens'
    __table_args__ = (db.UniqueConstraint('webinar_id', 'lect_id'), )

    id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars_added.webinar_id'), nullable=False)
    lect_id = db.Column(db.Integer, db.ForeignKey('users.lect_id'), nullable=True)
    token = db.Column(db.String(40), nullable=False)

    user = db.relationship('User')
    webinar = db.relationship('Webinar', back_populates='wtokens')

    def __repr__(self):
        return '<WebinarToken for #{0.lect_id} at #{0.webinar_id}>'.format(self)

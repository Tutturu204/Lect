from flask_restplus import fields
from lectarium_app import api

webinar_common_fields_model = api.model('webinar_post_model (abstract)', {
    'name': fields.String(required=True),
    'description': fields.String,
    'preview_url': fields.String,
    'is_closed': fields.Boolean(required=True),
    'subjects': fields.List(fields.String),
    'courses': fields.List(fields.String),
    'products': fields.List(fields.String),
})

webinar_post_planned_model = api.inherit('webinar_post_model (planned)', webinar_common_fields_model, {
    'webinar_type': fields.String(required=True, enum=('CLICKMEETING', 'YOUTUBE')),
    'begin_date': fields.DateTime(required=True),
    'duration': fields.String,
    'webinar_link': fields.String,
    'cm_account_login': fields.String,
    'message_for_students': fields.String,
})

webinar_post_uploaded_model = api.inherit('webinar_post_model (uploaded)', webinar_common_fields_model, {
    'webinar_type': fields.String(required=True, enum=('MANUALLY_UPLOADED', )),
    'vimeo_id': fields.String(required=True),
    'upload_date': fields.Date(required=True),
})

webinar_full_model = api.model('webinar (full)', {
    'webinar_id': fields.Integer(read_only=True),
    'room_id': fields.Integer(read_only=True),
    'name': fields.String,
    'description': fields.String,
    'preview_url': fields.String,
    'is_closed': fields.Boolean,
    'subjects': fields.List(fields.String),
    'courses': fields.List(fields.String),
    'products': fields.List(fields.String),
    'webinar_type': fields.String(enum=('CLICKMEETING', 'YOUTUBE', 'MANUALLY_UPLOADED')),
    'begin_date': fields.DateTime,
    'duration': fields.String,
    'webinar_link': fields.String,
    'cm_account_login': fields.String,
    'vimeo_id': fields.String,
    'upload_date': fields.Date,
    'initiator_lect_id': fields.Integer(read_only=True),
    'total_attendees': fields.Integer(read_only=True),
    'max_attendees': fields.Integer(read_only=True),
    'status': fields.String(read_only=True, enum=("CREATED", "PLANNED", "BEGINNING",
                                                  "IN_PROGRESS", "FINISHED", "UPLOADED", "AVAILABLE")),
})

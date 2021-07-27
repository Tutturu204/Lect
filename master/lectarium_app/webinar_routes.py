from lectarium_app.global_routes import webinar_nsp, pagination_parser
from flask_restplus import Resource
from flask import request, g
from lectarium_app import webinar_service, api
from lectarium_app.exceptions import StatusChangeError, ClmOperationalError
from lectarium_app.utils import PaginationMixin
from lectarium_app.serializers import webinar_full_model, webinar_post_planned_model, webinar_post_uploaded_model


@webinar_nsp.route("/update_status/<int:webinar_id>")
class WebinarsStatus(Resource):
    def post(self, webinar_id):
        status = request.get_json().get("status")
        try:
            return webinar_service.update_web_status(status, webinar_id)
        except StatusChangeError:
            api.abort(400)


@webinar_nsp.route('')
class WebinarCollection(Resource, PaginationMixin):
    BaseEntity = webinar_service.Webinar

    @api.expect(pagination_parser)
    @api.marshal_list_with(webinar_full_model)
    @privileges_required(clm_level=0)
    def get(self):
        """
        Получить список всех вебинаров
        """
        return self.paginate(pagination_parser.parse_args())


@webinar_nsp.route('/view')
class WebinarViewCollection(Resource, PaginationMixin):
    BaseEntity = webinar_service.Webinar

    @api.expect(pagination_parser)
    @api.marshal_list_with(webinar_full_model)
    @privileges_required(clm_level=0)
    def get(self):
        """
        Получить список всех вебинаров, доступных пользователю
        """
        #TODO: отдать в сервис с юзерами и получить проаннотированный is_payed ответ
        return self.paginate(pagination_parser.parse_args())


@webinar_nsp.route('/planned')
class WebinarPost(Resource):
    @api.expect(webinar_post_planned_model)
    @api.marshal_with(webinar_full_model)
    @privileges_required(clm_level=1)
    def post(self):
        """
        Создать вебинар
        """
        data = request.get_json()

        ok, reason = webinar_service.validate_webinar_post('planned', data)
        if not ok:
            api.abort(400, reason)

        webinar = webinar_service.create_webinar(data)
        # clm_service.create_webinars_tokens.submit(webinar.webinar_id)
        return webinar


@webinar_nsp.route('/uploaded')
class WebinarPost(Resource):
    @api.expect(webinar_post_uploaded_model)
    @api.marshal_with(webinar_full_model)
    @privileges_required(clm_level=1)
    def post(self):
        """
        Создать вебинар
        """
        data = request.get_json()

        ok, reason = webinar_service.validate_webinar_post('uploaded', data)
        if not ok:
            api.abort(400, reason)

        webinar = webinar_service.create_webinar(g.current_user, data)
        # clm_service.create_webinars_tokens.submit(webinar.webinar_id)
        return webinar


@webinar_nsp.route('/<int:webinar_id>')
class WebinarItem(Resource):
    @api.marshal_with(webinar_full_model)
    @privileges_required(clm_level=0)
    def get(self, webinar_id):
        """
        Получить один вебинар по его id
        """
        return webinar_service.get_webinar(webinar_id)

    @api.expect(webinar_full_model)
    @api.marshal_with(webinar_full_model)
    @privileges_required(clm_level=1)
    def patch(self, webinar_id):
        """
        Редактировать данные для одного вебинара
        """
        data = request.get_json()

        ok, reason = webinar_service.validate_webinar_patch(webinar_id, data)
        if not ok:
            api.abort(403, reason)

        webinar = webinar_service.update_webinar(webinar_id, data)
        return webinar


    @privileges_required(clm_level=1)
    def delete(self, webinar_id):
        """
        Удалить вебинар
        """

        ok, reason = webinar_service.validate_webinar_delete(webinar_id)
        if not ok:
            api.abort(403, reason)

        webinar_service.delete_webinar(webinar_id)
        return {}

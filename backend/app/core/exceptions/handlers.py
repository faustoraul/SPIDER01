from flask import jsonify


class ApiError(Exception):
    status_code = 400
    code = 'bad_request'

    def __init__(self, message=None, status_code=None, code=None, details=None):
        super().__init__(message or self.__class__.__name__)
        self.message = message or 'Error en la solicitud'
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details or {}

    def to_dict(self):
        payload = {'error': self.code, 'message': self.message}
        if self.details:
            payload['details'] = self.details
        return payload


class ValidationError(ApiError):
    status_code = 422
    code = 'validation_error'


class NotFoundError(ApiError):
    status_code = 404
    code = 'not_found'


class ConflictError(ApiError):
    status_code = 409
    code = 'conflict'


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify(error.to_dict()), error.status_code
#core/middleware.py

from .utils import is_pma_admin

class PMAAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        request.is_pma_admin = is_pma_admin(request.user) if request.user.is_authenticated else False

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
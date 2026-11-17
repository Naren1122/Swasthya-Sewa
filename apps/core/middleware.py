import logging
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    """
    Smart Global Exception Middleware for Dual-Engine Architecture (HTMX + DRF).
    
    Catches all uncaught server exceptions across the application and formats
    the response dynamically based on the client type:
    
    1. HTMX Client (`HX-Request: true`):
       Returns an Out-of-Band (OOB) DaisyUI toast alert with HTTP 500.
       HTMX automatically injects the toast into `#toast-container` without
       breaking the layout or replacing small partial targets with a full 500 page.
       
    2. DRF REST API Client (`/api/`):
       Returns a uniform, standardized JSON error envelope with HTTP 500.
       
    3. Standard Web Browser:
       Returns `None` to allow Django's root `handler500` to render the styled 500 page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Log the full exception traceback for debugging and audit
        logger.error(
            f"Unhandled Exception at {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={'user': getattr(request, 'user', None)}
        )

        # 1. Handle HTMX Requests
        if request.headers.get('HX-Request'):
            try:
                html = render_to_string('components/toast_error_oob.html', {
                    'error_message': 'An unexpected error occurred while processing your request. Please try again.'
                })
                return HttpResponse(html, status=500)
            except Exception as render_err:
                logger.critical(f"Failed to render HTMX error toast: {render_err}")
                return HttpResponse(
                    '<div id="toast-container" hx-swap-oob="beforeend">'
                    '<div class="alert alert-error text-white text-xs py-2 px-4 shadow rounded-xl">An unexpected error occurred.</div>'
                    '</div>',
                    status=500
                )

        # 2. Handle REST API Requests
        if request.path.startswith('/api/'):
            return JsonResponse({
                'success': False,
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected server error occurred. Please try again later.'
                }
            }, status=500)

        # 3. Standard Browser: Pass to Django's root handler500
        return None

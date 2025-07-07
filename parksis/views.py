import sys
import traceback

from django.http import HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render
from django.template import Context, loader


def custom_404(request, exception=None):
    """
    Custom 404 error handler
    """
    try:
        return render(
            request,
            "404.html",
            {
                "request_path": request.path,
                "exception": str(exception) if exception else None,
            },
            status=404,
        )
    except Exception:
        # Fallback in case template rendering fails
        return HttpResponseNotFound(
            "<h1>404 - Page Not Found</h1>"
            "<p>The requested page could not be found.</p>"
        )


def custom_500(request):
    """
    Custom 500 error handler
    """
    try:
        # Get exception information if available
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception_info = None

        if exc_value:
            exception_info = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value),
                "traceback": traceback.format_exc() if exc_traceback else None,
            }

        return render(
            request,
            "500.html",
            {
                "exception": (
                    exception_info["message"]
                    if exception_info
                    else "Internal Server Error"
                ),
                "exception_type": exception_info["type"] if exception_info else None,
                "debug_info": exception_info if exception_info else None,
            },
            status=500,
        )
    except Exception:
        # Fallback in case template rendering fails
        return HttpResponseServerError(
            "<h1>500 - Internal Server Error</h1>"
            "<p>An internal server error occurred.</p>"
        )


def raise_500_error(request):
    """
    Endpoint to raise a 500 error for testing purposes
    """
    raise Exception("This is a test exception to trigger a 500 error.")

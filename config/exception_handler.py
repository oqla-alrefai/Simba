from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Custom exception handler that always returns a 200 OK with a semantic body.

    - If DRF has already built a response (e.g. ValidationError), it will
      extract a readable message and return it in the standard {success,message}
      structure.
    - If an unexpected exception bubbles up, it will be caught and returned as
      a semantic error message without an HTTP error status.

    This is intentionally opinionated to match the frontend expectation of
    receiving semantic messages instead of HTTP status codes.
    """

    response = exception_handler(exc, context)
    message = "An error occurred"

    if response is not None:
        data = response.data
        if isinstance(data, dict):
            # Attempt to normalize DRF validation error structures.
            if "detail" in data:
                message = str(data.get("detail"))
            else:
                # Flatten first error value found.
                for value in data.values():
                    if value:
                        if isinstance(value, (list, tuple)):
                            message = ", ".join(str(v) for v in value)
                        else:
                            message = str(value)
                        break
        else:
            message = str(data)

        return Response({"success": False, "message": message})

    # Fallback for unhandled exceptions
    return Response({"success": False, "message": str(exc) or "Internal Server Error"})

from functools import wraps

from flask import g, request

from errors import AuthenticationError, AuthorizationError


def require_auth(auth_service, roles=None):
    allowed_roles = set(roles or [])

    def decorator(handler):
        @wraps(handler)
        def wrapped(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            scheme, _, token = header.partition(" ")
            if scheme.lower() != "bearer" or not token:
                raise AuthenticationError()

            user = auth_service.resolve_token(token)
            if allowed_roles and user.role not in allowed_roles:
                raise AuthorizationError()
            g.current_user = user
            return handler(*args, **kwargs)

        return wrapped

    return decorator

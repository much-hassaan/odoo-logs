import requests

from .exceptions import RequestException, AuthorizationException


class RESTBackend:
    """Wrapper around requests."""

    def __init__(self, base: str, headers: dict, integration, allowed_status=None):
        """
        :param base: base url
        """
        self.base = base
        self.headers = headers
        self.integration = integration

        if not allowed_status:
            allowed_status = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]
        self.allowed_status = allowed_status

    def get(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.get(*args, **kwargs))

    def head(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.head(*args, **kwargs))

    def post(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.post(*args, **kwargs))

    def patch(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.patch(*args, **kwargs))

    def put(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.put(*args, **kwargs))

    def delete(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.delete(*args, **kwargs))

    def options(self, *args, **kwargs):
        args, kwargs = self._extend_args(*args, **kwargs)
        return self._handle_response(requests.options(*args, **kwargs))

    def _extend_args(self, *args, **kwargs):
        args = list(args)

        # url
        if len(args):
            args[0] = self.base + args[0]
        if "url" in kwargs:
            kwargs["url"] = self.base + kwargs["url"]

        kwargs["headers"] = {**kwargs.get("headers", {}), **self.headers}

        return args, kwargs

    def _handle_response(self, response: requests.Response):
        """Calls correct handler method. E.g. if the status code is 404, it calls
        handle_404(response)
        """
        if response.status_code not in self.allowed_status:
            handler = getattr(self, f"_handle_{str(response.status_code)}", None)
            if not handler:
                handler = self._default_handler
            return handler(response)
        return response

    def _default_handler(self, response: requests.Response):
        raise self.integration.ihub_error(
            summary=f"[{response.status_code}] calling {response.request.method} on {response.request.url}\n",
            details=self._details(response),
            raised=True,
        )

    def _handle_401(self, response: requests.Response):
        raise self.integration.ihub_error(
            summary=f"Authorization error [{response.status_code}] on {response.request.url}\n",
            details=self._details(response),
            raised=True,
        )

    @staticmethod
    def _details(response: requests.Response):
        if response.headers.get("content-type") == "application/json":
            return response.json()
        return response.content.decode("UTF-8")

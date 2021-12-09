from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from opentelemetry.propagators.b3 import B3MultiFormat
from starlette.middleware.base import BaseHTTPMiddleware

from telemetrytest.services import JaegerTracerProvider

from .containers import Container


@inject
class OpenTracingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, tracer: JaegerTracerProvider = Depends(Provide[Container.tracer])):
        super().__init__(app)
        self._tracer_provider = tracer

    async def dispatch(self, request, call_next):
        method = str(request.url)
        method = method.replace(str(request.base_url), "")

        propagator = B3MultiFormat()
        context = propagator.extract(request.headers)
        with self._tracer_provider.start_span("Receiving {method} call to '{url}'".format(
                method=request.method,
                url=method), context):
            response = await call_next(request)
            return response

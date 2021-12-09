from datetime import date
from typing import Optional

import requests
from dependency_injector.wiring import inject, Provide
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import StatusCode, Status
from requests import RequestException

from opentelemetry.propagators.b3 import B3MultiFormat

from tinyrpc import RPCClient, RPCError
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport


class JaegerTracerProvider:
    def __init__(self, service_name: str, host_name: str, port: int):
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({SERVICE_NAME: service_name})
            )
        )

        jaeger_exporter = JaegerExporter(
            agent_host_name=host_name,
            agent_port=port,
        )

        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )

        self.tracer = trace.get_tracer(__name__)

    def start_span(self, name: str, context: Optional[Context] = None):
        return self.tracer.start_as_current_span(name, context)

    def get_span(self) -> Span:
        return trace.get_current_span()


@inject
class InjectableRPCClient:
    def __init__(self, trace_provider: JaegerTracerProvider = Provide["tracer"]):
        server = RPCClient(JSONRPCProtocol(), HttpPostClientTransport('http://localhost:8080'))
        self._client = server.get_proxy()
        self._trace_provider = trace_provider

    def get_holidays(self, date_from: date, date_to: date):
        with self._trace_provider.start_span("Calling calendar: get_holidays"):
            serialized_from = date_from.strftime("%Y-%m-%d")
            serialized_to = date_to.strftime("%Y-%m-%d")
            span = self._trace_provider.get_span()
            span.set_attribute("HTTP_METHOD", 'JSONRPC')
            span.set_attribute("HTTP_URL", 'get_holidays')
            span.add_event('Created request')
            try:
                res = self._client.get_holidays(serialized_from, serialized_to)
                span.add_event('Received response: {}'.format(res))
                return res
            except RPCError as e:
                span.add_event('Received error: {}'.format(e))
                return None


@inject
class InjectableHttpClient:
    def __init__(self, trace_provider: JaegerTracerProvider = Provide["tracer"]):
        self._trace_provider = trace_provider

    def call_method(self, host: str, method: str):
        with self._trace_provider.start_span("Calling {url}: {method}".format(url=host, method=method)):
            span = self._trace_provider.get_span()
            context = span.get_span_context()
            try:
                url = host + "/" + method
                if host[:7] != "http://":
                    url = "http://" + url
                headers = {
                    'Host': host,
                    'User-Agent': 'shapython/0.0.1'
                }
                propagator = B3MultiFormat()
                propagator.inject(headers)
                span.add_event('Request headers', headers)
                span.add_event('Request body', {'Body': "None, it's a get method"})

                response = requests.get(url, headers=headers)
                print("response is {}".format(response.content))

                span.add_event('Response headers', response.headers)
                span.add_event('Response body', response.json())
                span.set_status(Status(StatusCode.OK))
                return response.json()
            except ConnectionError:
                span.set_status(Status(StatusCode.ERROR, "No connection"))
            except TimeoutError:
                span.set_status(Status(StatusCode.ERROR, "Connection timed out"))
            except RequestException as ex:
                span.set_status(Status(StatusCode.ERROR, str(ex)))


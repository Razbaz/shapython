from dependency_injector import containers, providers

from .services import JaegerTracerProvider, InjectableRPCClient, InjectableHttpClient


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[".actions", ".middleware"])

    tracer = providers.Singleton(JaegerTracerProvider, service_name="crocodeal", host_name="localhost", port=6831)
    rpc_client = providers.Factory(InjectableRPCClient)
    http_client = providers.Factory(InjectableHttpClient)

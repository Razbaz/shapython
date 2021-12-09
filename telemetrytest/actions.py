from datetime import date

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, APIRouter

from .services import JaegerTracerProvider, InjectableRPCClient, InjectableHttpClient
from .containers import Container


router = APIRouter()


@router.get("/lol")
@inject
def get_something(
        tracer_provider: JaegerTracerProvider = Depends(Provide[Container.tracer]),
        rpc_client: InjectableRPCClient = Depends(Provide[Container.rpc_client])):
    # with tracer_provider.tracer.start_as_current_span("action level"):
    date_from: date = date(2020, 5, 1)
    date_to = date(2020, 6, 1)
    reply = rpc_client.get_holidays(date_from, date_to)
    return reply


@router.get("/step1")
@inject
def step_1(
        http_client: InjectableHttpClient = Depends(Provide[Container.http_client])):
    reply = http_client.call_method("localhost:81", "step2")
    return reply


@router.get("/step3")
@inject
def step_3(
        http_client: InjectableHttpClient = Depends(Provide[Container.http_client])):
    reply = http_client.call_method("localhost:81", "step4")
    return reply

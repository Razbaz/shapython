from fastapi import FastAPI

from .containers import Container
from .actions import router
from .middleware import OpenTracingMiddleware


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI()
    app.container = container
    app.include_router(router)
    app.add_middleware(OpenTracingMiddleware)
    return app


main_api = create_app()

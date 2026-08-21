import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response
from contextlib import asynccontextmanager
from atlas.routing.registry import ServiceRoute,ServiceRegistry
from atlas.main_settings import settings
from atlas.routing.seed import initialize_route_registry
from atlas.auth.jwt import AuthenticatedUser, require_authenticated_user
from atlas.auth.authorization import require_service_access
from atlas.middleware.request_id import RequestIDMiddleware


# GENERATOR FUNCTION FOR LIFESPAN EVENT
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_route_registry()
    app.state.service_registry = ServiceRegistry()
    app.state.service_registry.load()
    app.state.http_client = httpx.AsyncClient(timeout=settings.downstream_timeout_seconds)
    
    yield 
    await app.state.http_client.aclose()




app = FastAPI(title="Atlas", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
HOP_BY_HOP_HEADERS = {"connection", "host", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}


async def forward_request(
    service: str,
    request: Request,
    path: str = "",
    _: AuthenticatedUser = Depends(require_authenticated_user),) -> Response:
    
    """Forward supported API requests to the configured downstream service."""
    route = request.app.state.service_registry.get(service)
    
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")

    base_url, downstream_prefix = route.base_url, route.path_prefix
    target_url = f"{base_url}{downstream_prefix}"
    
    if path:
        target_url = f"{target_url}/{path}"
        
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    request_headers = {
        name: value
        for name, value in request.headers.items()
        if name.lower() not in HOP_BY_HOP_HEADERS
    }
    request_headers["X-Request-ID"] = request.state.request_id

    try:
        client =request.app.state.http_client
        downstream_response = await client.request(
                method=request.method,
                url=target_url,
                headers=request_headers,
                content=await request.body(),
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to reach downstream service") from None

    response_headers = {
        name: value
        for name, value in downstream_response.headers.items()
        if name.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=response_headers,
    )

def register_proxy_route(
    app: FastAPI,
    path: str,
    endpoint,
    methods: list[str],
    name_prefix: str,
    dependencies: list | None = None,
) -> None:
    """Register one FastAPI route per HTTP method."""

    for method in methods:
        app.add_api_route(
            path,
            endpoint,
            methods=[method],
            operation_id=f"{name_prefix}_{method.lower()}",
            dependencies=dependencies,
        )





# /api/{service}
register_proxy_route(
    app,
    "/api/{service}",
    forward_request,
    PROXY_METHODS,
    "forward_service",
    [Depends(require_service_access)], 
)

# /api/{service}/{path:path}
register_proxy_route(
    app,
    "/api/{service}/{path:path}",
    forward_request,
    PROXY_METHODS,
    "forward_service_path",
    [Depends(require_service_access)],
)

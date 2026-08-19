import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from contextlib import asynccontextmanager
from fastapi import FastAPI
from atlas.routing.registry import ServiceRoute,ServiceRegistry
from atlas.main_settings import settings



# GENERATOR FUNCTION FOR LIFESPAN EVENT
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=settings.downstream_timeout_seconds)
    
    yield 
    await app.state.http_client.aclose()




app = FastAPI(title="Atlas", lifespan=lifespan)

service_registry = ServiceRegistry({
    "patients": ServiceRoute(
        settings.patient_service_url,
        "/patients",
    ),
    "doctors": ServiceRoute(
        settings.doctor_service_url,
        "/doctors",
    ),
    "medicines": ServiceRoute(
        settings.medicine_service_url,
        "/medicines",
    )
})



PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
HOP_BY_HOP_HEADERS = {"connection", "host", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}



@app.api_route("/api/{service}", methods=PROXY_METHODS)
@app.api_route("/api/{service}/{path:path}", methods=PROXY_METHODS)
async def forward_request(service: str, request: Request, path: str = "") -> Response:
    """Forward supported API requests to the configured downstream service."""
    route = service_registry.get(service)
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

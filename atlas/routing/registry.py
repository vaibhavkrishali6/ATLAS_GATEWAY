from dataclasses import dataclass

#service route class to hold the base url and path prefix for a service
@dataclass(frozen=True)
class ServiceRoute:
    base_url: str
    path_prefix: str


class ServiceRegistry:
    def __init__(self, services: dict[str, ServiceRoute]):
        self.services = services

    def get(self, service: str) -> ServiceRoute | None:
        return self.services.get(service)
    
    
from dataclasses import dataclass
from sqlalchemy import select
from atlas.database.database import SessionLocal
from atlas.routing.models import Route

#service route class to hold the base url and path prefix for a service
@dataclass(frozen=True)
class ServiceRoute:
    base_url: str
    path_prefix: str


class ServiceRegistry:
    def __init__(self):
        self.services:dict[str, ServiceRoute] = {}
    
    def load(self)-> None:
        """Load the service registry from the database."""
        # This method can be implemented to load services from the database if needed.
        with SessionLocal() as session:
            routes=session.scalars(
                    select(Route).where(Route.active.is_(True))).all()

            self.services = {
                route.service_name: ServiceRoute(
                    base_url=route.base_url,
                    path_prefix=route.path_prefix,
                )
                for route in routes
            }
            
    def get(self, service: str) -> ServiceRoute | None:
        return self.services.get(service)
    
    
    
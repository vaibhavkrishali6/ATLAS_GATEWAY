"""Initial database setup for the built-in Atlas service routes."""

import logging

from sqlalchemy import select

from atlas.database.database import Base, SessionLocal, engine
from atlas.main_settings import settings
from atlas.routing.models import Route

logger = logging.getLogger(__name__)


def initialize_route_registry() -> None:
    """Create the routes table and add built-in routes if they are missing."""
    Base.metadata.create_all(bind=engine)

    configured_routes = (
        ("patients", settings.patient_service_url, "/patients"),
        ("doctors", settings.doctor_service_url, "/doctors"),
        ("medicines", settings.medicine_service_url, "/medicines"),
    )

    with SessionLocal() as session:
        existing_names = set(session.scalars(select(Route.service_name)).all())
        for service_name, base_url, path_prefix in configured_routes:
            if service_name not in existing_names:
                session.add(
                    Route(
                        service_name=service_name,
                        base_url=base_url,
                        path_prefix=path_prefix,
                    )
                )
        session.commit()

        route_names = session.scalars(
            select(Route.service_name).where(Route.active.is_(True)).order_by(Route.id)).all()
    logger.info("Route registry ready with active routes: %s", ", ".join(route_names))

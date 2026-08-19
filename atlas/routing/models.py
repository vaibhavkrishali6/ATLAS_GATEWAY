"""Persistent route definitions used by the Atlas gateway."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from atlas.database.database import Base


class Route(Base):
    """A downstream service route stored in PostgreSQL's ``routes`` table."""

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    path_prefix: Mapped[str] = mapped_column(String(500), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
     DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()                                               
    )

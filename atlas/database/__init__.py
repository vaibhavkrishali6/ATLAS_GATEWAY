"""Database setup shared by the Atlas gateway."""

from .database import Base, SessionLocal, engine

__all__ = ["Base", "SessionLocal", "engine"]

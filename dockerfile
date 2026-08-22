FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv

RUN uv sync --frozen

COPY atlas ./atlas
COPY services ./services

RUN mkdir -p /app/logs

EXPOSE 8000 8001 8002 8003 8004

CMD ["uv", "run", "uvicorn", "atlas.main:app", "--host", "0.0.0.0", "--port", "8000"]
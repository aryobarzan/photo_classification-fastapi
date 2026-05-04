FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
# --mount=type=cache,target=/root/.cache/pip allows caching of pip packages between builds
# Also: we use the CPU version of torch for a smaller build size
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

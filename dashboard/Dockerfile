FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn aiohttp jinja2
COPY . /app
EXPOSE 8200
CMD ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8200"]

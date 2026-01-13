FROM python:3.11-slim
WORKDIR /app
COPY ../../requirements_min.txt /app/requirements_min.txt
RUN pip install --no-cache-dir -r /app/requirements_min.txt
COPY . /app/cloud/processor
EXPOSE 5000
CMD ["python", "cloud/processor/main.py"]

FROM python:3.11-slim
WORKDIR /app
COPY ../../requirements_min.txt /app/requirements_min.txt
RUN pip install --no-cache-dir -r /app/requirements_min.txt
COPY . /app/agents/edge_agent
EXPOSE 8100
CMD ["uvicorn", "agents.edge_agent.app:app", "--host", "0.0.0.0", "--port", "8100"]

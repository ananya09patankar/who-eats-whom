FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY dagster_project ./dagster_project
ENV PYTHONUNBUFFERED=1
EXPOSE 3000
CMD ["dagster", "dev", "-m", "dagster_project", "-h", "0.0.0.0", "-p", "3000"]

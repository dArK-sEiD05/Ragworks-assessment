FROM python:3.11-slim
WORKDIR /app
COPY user-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY user-service/ .
COPY shared /app/shared
ENV PYTHONPATH=/app
CMD ["python", "main.py"]

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py nlu_parallel.py .

EXPOSE 8001

CMD ["python", "app.py"]
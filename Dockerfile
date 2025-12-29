FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt

COPY src/server_monitoring.py /app/server_monitoring.py

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "-u", "server_monitoring.py"]
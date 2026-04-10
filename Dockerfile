FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:9000", "-w", "2", "--timeout", "120"]

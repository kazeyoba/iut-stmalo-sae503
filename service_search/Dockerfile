FROM python:3.9.21-bookworm

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY app /app

WORKDIR /app

CMD ["python3", "app.py"]
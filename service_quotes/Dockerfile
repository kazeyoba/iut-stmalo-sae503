FROM python:3.11.11-bookworm

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY app /app

WORKDIR /app

EXPOSE 5000

CMD ["python3", "app.py"]
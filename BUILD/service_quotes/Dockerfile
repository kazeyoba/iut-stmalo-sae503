FROM python:3.11.11-alpine3.20

ENV PATH="/home/haddok/.local/bin:${PATH}"

RUN adduser -D haddok

USER haddok

WORKDIR /home/worker

COPY --chown=haddok:haddok requirements.txt requirements.txt

RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=haddok:haddok app .

EXPOSE 5000

CMD ["python3", "app.py"]
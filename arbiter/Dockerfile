FROM python:3.10-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install fastapi
RUN pip install "uvicorn[standard]"
RUN pip install psycopg2-binary

COPY . .

CMD ["uvicorn","--reload", "main:app", "--host", "0.0.0.0"]
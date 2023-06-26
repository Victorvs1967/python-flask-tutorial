FROM python:3.11

WORKDIR /app

COPY requirements.txt /app

RUN pip3 install -U pip -r requirements.txt

COPY . /app

EXPOSE 8000
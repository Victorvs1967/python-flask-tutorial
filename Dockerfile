FROM python:3.11

WORKDIR /backend
COPY requirements.txt /backend
RUN pip3 install -U pip -r requirements.txt
COPY . /backend

EXPOSE 8000
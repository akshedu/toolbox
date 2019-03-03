FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /src
WORKDIR /src
ADD . /src/
RUN pip install -r requirements/local.txt

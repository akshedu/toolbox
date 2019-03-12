FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /src
WORKDIR /src
ADD requirements/ /src/requirements/
RUN pip install -r requirements/production.txt

ADD . /src/

CMD /src/docker-entrypoint-web.sh
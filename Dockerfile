FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /src
WORKDIR /src
ADD requirements/ /src/requirements/
RUN pip install -r requirements/local.txt

ADD . /src/

CMD /src/docker-entrypoint-web.sh
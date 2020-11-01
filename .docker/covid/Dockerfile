ARG BASE_IMAGE=ubuntu:20.04
ARG PORT=8080
FROM ${BASE_IMAGE}

# Install python3.8
RUN apt-get update  \
    && DEBIAN_FRONTEND=noninteractive apt install -yq \
       gcc\
       g++\
       git\
       curl\
       nano\
       libblas-dev\
       liblapack-dev\
       software-properties-common\
       locales\
       cron

RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 
ENV LANG en_US.utf8

RUN add-apt-repository -y ppa:deadsnakes/ppa  \
    && apt-get update  \
    && apt install -yq python3.8-dev \
       python3-distutils\
    && ln -s /usr/bin/python3.8 /usr/bin/python || true \
    && curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py  \
    && python /tmp/get-pip.py 

RUN rm -rf /tmp/* /root/.cache/* \
    && rm -rf /var/lib/apt/lists/* 


# Install flask requirements
COPY ./flask/requirements.txt /tmp
RUN cat /tmp/requirements.txt | xargs --no-run-if-empty -n 1 python -m pip install

# Install src requirements
COPY ./src/requirements.txt /tmp
RUN cat /tmp/requirements.txt | xargs --no-run-if-empty -n 1 python -m pip install

COPY ./src/ /src
RUN python -m pip install /src
RUN rm -rf /tmp/* /root/.cache/* \
    && rm -rf /src

RUN rm -rf /tmp/* /root/.cache/*

COPY ./flask /app

WORKDIR /app/

RUN mv /app/crontab /etc/cron.d/updatetask
RUN chmod 0644 /etc/cron.d/updatetask
RUN service cron start

CMD service cron start && /bin/bash /app/flask.sh ${PORT}


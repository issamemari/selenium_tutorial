# syntax=docker/dockerfile:1

FROM python:3.9

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

RUN apt-get -y update
RUN apt-get install -y google-chrome-stable


RUN apt-get install -yqq unzip

RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip

RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

ENV DISPLAY=:99

WORKDIR /app

RUN pip3 install --upgrade pip

RUN useradd -u 8877 issa

RUN chown -R issa:issa /app
RUN mkdir /home/issa
RUN chown -R issa:issa /home/issa

USER issa

COPY --chown=issa:issa requirements.txt requirements.txt

ENV PATH="/home/issa/.local/bin:${PATH}"

RUN pip3 install -r requirements.txt

COPY --chown=issa:issa . .

ENTRYPOINT ["python","src/main.py"]

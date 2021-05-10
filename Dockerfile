FROM python:alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apk add --no-cache bash build-base capstone-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install bs4 capstone dnspython


WORKDIR /usr/src/app

VOLUME /var/lib/nemubot

RUN apk add --no-cache mandoc-doc man-db w3m youtube-dl

COPY . .

ENTRYPOINT [ "python", "-m", "nemubot", "-d", "-P", "", "-M", "/usr/src/app/modules" ]
CMD [ "-D", "/var/lib/nemubot" ]
FROM python:alpine as pybuild

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apk add --no-cache bash build-base capstone-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install bs4 capstone dnspython


FROM python:alpine

RUN apk add --no-cache capstone w3m

WORKDIR /usr/src/app

VOLUME /var/lib/nemubot

COPY requirements.txt ./

COPY --from=pybuild /usr/lib/python3.9 /usr/lib/python3.9
COPY . .

ENTRYPOINT [ "python", "-m", "nemubot", "-d", "-M", "/usr/src/app/modules" ]
CMD [ "-D", "/var/lib/nemubot" ]
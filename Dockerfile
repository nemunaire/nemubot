FROM python:alpine

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN apk add --no-cache bash build-base capstone-dev mandoc-doc man-db w3m youtube-dl aspell aspell-fr && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install bs4 capstone dnspython && \
    apk del build-base capstone-dev && \
    ln -s /var/lib/nemubot/home /home/nemubot

VOLUME /var/lib/nemubot

COPY . /usr/src/app/

RUN ./setup.py install

WORKDIR /var/lib/nemubot
USER guest
ENTRYPOINT [ "python", "-m", "nemubot", "-d", "-P", "", "-M", "/usr/src/app/modules" ]
CMD [ "-D", "/var/lib/nemubot" ]
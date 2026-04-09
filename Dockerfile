FROM python:3.9-alpine

RUN apk add --no-cache tor

RUN echo "SOCKSPort 9050" > /etc/tor/torrc \
    && echo "ControlPort 9051" >> /etc/tor/torrc \
    && echo "CookieAuthentication 0" >> /etc/tor/torrc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tor.py .

EXPOSE 9050 9051

CMD tor & python tor.py 5
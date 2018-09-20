FROM python:2.7-alpine

ADD requirements.txt /
RUN pip install -r requirements.txt
COPY templates /templates
ADD main.py /
EXPOSE 5000
CMD gunicorn -w 2 -b 0.0.0.0:5000 main:app
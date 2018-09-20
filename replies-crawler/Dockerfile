FROM python:2.7-alpine

RUN mkdir /private
VOLUME /private
ADD requirements.txt /
RUN pip install -r requirements.txt
ADD crawler.py /

ENTRYPOINT ["python", "./crawler.py"]
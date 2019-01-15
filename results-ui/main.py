import logging
import os

import google
from flask import Flask, render_template, json
from google.cloud import storage

app = Flask(__name__)

BUCKET_NAME = os.environ.get("BUCKET_NAME", "twitter-users-test")
GEOBUCKET_NAME = os.environ.get("GEOBUCKET_NAME", "geo-user-timelines")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
    level=logging.INFO
)

PRODUCTION = os.environ.get('PRODUCTION', False)


def _get_uploaded_users(bucket_name, folder, event=None):
    logging.info('Getting uploaded users %s...' % bucket_name)
    cli = storage.Client()
    try:
        bucket = cli.get_bucket(bucket_name)
        d = []
        for blob in bucket.list_blobs():
            splitted = blob.name.split('/')
            if len(splitted) < 4:
                continue
            if event and event != splitted[1]:
                continue
            url = 'https://storage.googleapis.com/%s/%s/%s/%s/%s' % (
                bucket_name, folder, splitted[1], splitted[2], splitted[3]
            )
            d.append({'event': splitted[1], 'status': splitted[2], 'user': splitted[3], 'url': url})
        return d
    except google.cloud.exceptions.NotFound:
        logging.error('Bucket %s does not exist!' % BUCKET_NAME)
    return {}


def _get_uploaded_events(bucket_name):
    logging.info('Getting uploaded events %s...' % bucket_name)
    cli = storage.Client()
    try:
        bucket = cli.get_bucket(bucket_name)
        d = set()
        for blob in bucket.list_blobs():
            splitted = blob.name.split('/')
            if len(splitted) < 4:
                continue
            d.add(splitted[1])
        return {'events': list(d)}
    except google.cloud.exceptions.NotFound:
        logging.error('Bucket %s does not exist!' % BUCKET_NAME)
    return {}


@app.route('/')
def home():
    return render_template('home.html', event='')


@app.route('/event/<event>')
def home_event(event):
    return render_template('users.html', event=event)


@app.route('/geo/event/<event>')
def geohome_event(event):
    return render_template('geo_users.html', event=event)


@app.route('/data/')
def get_data():
    return json.dumps(_get_uploaded_users(BUCKET_NAME, 'results'))


@app.route('/data/<event>')
def get_data_event(event=''):
    return json.dumps(_get_uploaded_users(BUCKET_NAME, 'results', event=event))


@app.route('/geodata/')
def get_geodata():
    return json.dumps(_get_uploaded_users(GEOBUCKET_NAME, 'georesults'))


@app.route('/geodata/<event>')
def get_geodata_event(event):
    return json.dumps(_get_uploaded_users(GEOBUCKET_NAME, 'georesults', event=event))


@app.route('/events/')
def overall_events():
    return json.dumps(_get_uploaded_events(BUCKET_NAME))


if __name__ == "__main__":
    app.run(debug=not PRODUCTION, host='0.0.0.0')

import logging
import os
import re

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


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value


def _get_uploaded_users(bucket_name, folder):
    logging.info('Getting uploaded users %s...' % bucket_name)
    cli = storage.Client()
    try:
        bucket = cli.get_bucket(bucket_name)
        d = []
        for blob in bucket.list_blobs():
            splitted = blob.name.split('/')
            if len(splitted) < 4:
                continue
            url = 'https://storage.googleapis.com/%s/%s/%s/%s/%s' % (
            bucket_name, folder, splitted[1], splitted[2], splitted[3])
            d.append({'event': splitted[1], 'status': splitted[2], 'user': splitted[3], 'url':url})
        return d
    except google.cloud.exceptions.NotFound:
        logging.error('Bucket %s does not exist!' % BUCKET_NAME)
    return {}


@app.route('/')
def home():
    return render_template('users.html')


@app.route('/geo')
def geohome():
    return render_template('geo_users.html')


@app.route('/data')
def get_data():
    return json.dumps(_get_uploaded_users(BUCKET_NAME, 'results'))


@app.route('/geodata')
def get_geodata():
    return json.dumps(_get_uploaded_users(GEOBUCKET_NAME, 'georesults'))


if __name__ == "__main__":
    app.run(debug=not PRODUCTION, host='0.0.0.0')

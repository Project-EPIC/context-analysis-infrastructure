import logging
import os
import re

from flask import Flask, request, json, render_template
from kafka import KafkaProducer


app = Flask(__name__)

TOPIC = os.environ.get('KAFKA_TOPIC', 'tw_users')
SERVERS = os.environ.get('KAFKA_SERVERS', 'localhost')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
    level=logging.INFO
)

PRODUCTION = os.environ.get('PRODUCTION', False)
PRODUCER = KafkaProducer(bootstrap_servers=SERVERS)

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


@app.route('/')
def home():
    return render_template('submit.html')


def _generate_user_string(end_date, event, start_date, user, extended=False):
    return user + ',' + event + ',' + start_date + ',' + end_date + ',' + str(extended)


@app.route('/submit', methods=['POST'])
def submit():
    event = slugify(request.form.get('event', None))
    if not event:
        return json.dumps({'type': 'error', 'message': 'Missing event'})
    start_date, end_date = request.form.get('daterange', '-').split('-')
    if not start_date or not end_date:
        return json.dumps({'type': 'error', 'message': 'Missing date range'})
    users = request.form.get('users', None)
    if not users:
        return json.dumps({'type': 'error', 'message': 'Missing users'})
    extended = request.form.get('extended', 'false').lower() == 'true'
    for user in users.split(','):
        user = slugify(user)
        user_string = _generate_user_string(end_date, event, start_date, user, extended)
        PRODUCER.send(TOPIC, bytes(user_string))
    return json.dumps({'type': 'success', 'message': 'Users added to queue'})


if __name__ == "__main__":
    app.run(debug=not PRODUCTION, host='0.0.0.0')

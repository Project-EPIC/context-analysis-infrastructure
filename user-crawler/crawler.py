import argparse
import errno
import json
import logging
import sys
import time
from datetime import datetime

import google
import os
import re
import tweepy
from google.cloud import storage
from google.cloud.storage import Bucket
from kafka import KafkaConsumer
from tweepy import OAuthHandler, Cursor, API, TweepError

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "ENTER YOUR ACCESS TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET", "ENTER YOUR ACCESS TOKEN SECRET")
CONSUMER_KEY = os.environ.get("CONSUMER_KEY", "ENTER YOUR API KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET", "ENTER YOUR API SECRET")

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = API(auth)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
GEORESULTS_DIR = os.path.join(BASE_DIR, 'georesults')
logging.basicConfig(
    format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
    level=logging.INFO
)
logging.info('Saving results at %s' % RESULTS_DIR)


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


def _get_bucket(bucket_name):
    logging.info('Getting bucket %s...' % bucket_name)
    cli = storage.Client()
    try:
        bucket = cli.get_bucket(bucket_name)
    except google.cloud.exceptions.NotFound:
        logging.warn('Bucket %s does not exist!' % bucket_name)
        logging.info('Creating bucket %s...' % bucket_name)
        bucket = cli.create_bucket(bucket_name)
        logging.info('Creating bucket %s...Done' % bucket_name)
    logging.info('Getting bucket %s...Done' % bucket_name)

    assert isinstance(bucket, Bucket)
    return bucket


def _blob_exists(filename, bucket):
    logging.info('Checking if file %s already uploaded to %s...' % (filename, bucket.name))
    rel_path = os.path.relpath(filename, BASE_DIR)
    blob = bucket.blob(rel_path)
    if blob.exists():
        logging.info('Checking if file %s already uploaded to %s...Already there' % (filename, bucket.name))
        return True
    logging.info('Checking if file %s already uploaded to %s...Not there' % (filename, bucket.name))
    return False


def _upload_file_gcloud(filename, bucket, verbose=True):
    logging.info('Uploading file to bucket %s...' % bucket.name)
    rel_path = os.path.relpath(filename, BASE_DIR)
    blob = bucket.blob(rel_path)
    if not blob.exists():
        blob.upload_from_filename(filename)
        blob.make_public()
        logging.info('Uploading file to bucket %s...Done' % bucket.name)

    else:
        logging.warn('File already exists! Filename: %s. Skipping!' % rel_path)


def _ensure_folder_exists(filename):
    if not os.path.dirname(filename):
        return
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def _generate_filename(user, event, status):
    event = event or 'no_event'
    path = os.path.join(RESULTS_DIR, event)
    if status:
        path = os.path.join(path, status)
    return os.path.join(path, user + '.json')


def _generate_geofilename(user, event, status):
    event = event or 'no_event'
    path = os.path.join(GEORESULTS_DIR, event)
    if status:
        path = os.path.join(path, status)
    return os.path.join(path, user + '.geojson')


def _twitter_errors_handler(cursor):
    user_accessible = True
    while user_accessible:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            logging.warn('Rate limit reached! Sleeping for 15 minutes. Good night, be back in a bit!')
            time.sleep(15 * 60)
        except TweepError as e:
            if not '=' in e.reason:
                raise
            api_code = int(e.reason.split('=')[1].replace(' ', ''))
            if api_code == 429:
                logging.warn('Rate limit reached! Sleeping for 2 minutes. Good night, be back in a bit!')
                time.sleep(2 * 60)
            elif api_code == 404:
                logging.warn('Non-existing user: %s' % cursor.kargs.get('id'))
                user_accessible = False
            elif api_code == 401:
                logging.warn('Protected user: %s' % cursor.kargs.get('id'))
                user_accessible = False
            elif api_code >= 500:
                logging.warn(
                    'Oops seems like we got a %d error from twitter, let\'s check again in 10 seconds' % api_code)
                time.sleep(10)
            else:
                raise


def _unpack(input_line):
    d_format = '%m/%d/%Y'
    input_line = input_line.replace(' ', '').replace('\n', '')
    try:
        user, event, start_date, end_date, extended = input_line.split(',')
        return user, event, datetime.strptime(start_date, d_format), datetime.strptime(end_date, d_format), \
               extended.lower() == 'true'
    except ValueError:
        pass
    try:
        user, event, start_date, end_date = input_line.split(',')
        return user, event, datetime.strptime(start_date, d_format), datetime.strptime(end_date, d_format), False
    except ValueError:
        pass
    try:
        user, event, start_date = input_line.split(',')
        return user, event, datetime.strptime(start_date, d_format), None, False
    except ValueError:
        pass
    try:
        user, event, _, _ = input_line.split(',')
        return user, event, None, None, False
    except ValueError:
        pass
    try:
        user, event, _ = input_line.split(',')
        return user, event, None, None, False
    except ValueError:
        pass
    try:
        user, event = input_line.split(',')
        return user, event, None, None, False
    except ValueError:
        pass
    return input_line, None, None, None, False


def _generate_status(before_start_date, before_end_date, non_accessible):
    if non_accessible:
        return 'not_accessible'
    if before_start_date:
        return 'complete'
    if before_end_date:
        return 'incomplete'
    return 'failed'


def _tweet_to_feature(tweet):
    # Handle geo/coordinate info
    geo = None
    if 'coordinates' in tweet:
        if tweet['coordinates']:
            geo = tweet['coordinates']
    else:
        if 'geo' in tweet:
            if tweet['geo']:
                geo = {'type': 'Point',
                       'coordinates': reversed(tweet['geo']['coordinates'])}
    return {
               'type': 'Feature',
               'properties': {
                   'user': tweet['user']['screen_name'],
                   'date': tweet['created_at'],
                   'text': tweet['text'] if 'text' in tweet else tweet['full_text'],
                   'tweetID': tweet['id_str']
               },
               'geometry': geo
           }, geo


ALL_STATUS = ['not_accessible', 'complete', 'incomplete', 'failed']


def pull_user_timeline(input_line, is_geo_enabled=True):
    user, event, start_date, end_date, extended = _unpack(input_line)
    user = slugify(user)
    logging.info('Pulling tweets for %s...' % user)
    if extended:
        cursor = Cursor(api.user_timeline, id=user, count=200, tweet_mode='extended')
    else:
        cursor = Cursor(api.user_timeline, id=user, count=200)
    filename = _generate_filename(user, None, None)
    geofilename = _generate_geofilename(user, None, None)
    _ensure_folder_exists(filename)
    _ensure_folder_exists(geofilename)
    before_start_date = False
    before_end_date = False
    non_accessible = True
    geo_count = 0
    with open(filename, 'w') as f, open(geofilename, 'w') as gf:
        for n_page, page in enumerate(_twitter_errors_handler(cursor.pages())):
            non_accessible = False

            logging.info('Parsing page %d...' % n_page)
            logging.info('Tweets downloaded: %d' % len(page))
            for tweet in page:
                json.dump(tweet._json, f)
                f.write("\n")

                if start_date and not before_start_date:
                    before_start_date = tweet.created_at < start_date
                if end_date and not before_end_date:
                    before_end_date = tweet.created_at < end_date
                if not is_geo_enabled:
                    continue
                feature, is_geo = _tweet_to_feature(tweet._json)
                if is_geo:
                    geo_count += 1
                assert feature
                json.dump(feature, gf)
                gf.write("\n")
            logging.info('Parsing page %d...Done' % n_page)

    status = _generate_status(before_start_date, before_end_date, non_accessible)
    logging.info('Status for %s is %s' % (user, status))

    if start_date or end_date:
        classified_filename = _generate_filename(user, event, status)
        classified_geofilename = _generate_geofilename(user, event, status)
    else:
        classified_filename = _generate_filename(user, event, 'no_date')
        classified_geofilename = _generate_geofilename(user, event, 'no_date')
    _ensure_folder_exists(classified_filename)
    os.rename(filename, classified_filename)
    if geo_count:
        _ensure_folder_exists(classified_geofilename)
        with open(geofilename, 'r') as inp, open(classified_geofilename, 'w') as out:
            out.write('{"type": "FeatureCollection", "features":[')
            first = True
            for l in inp:
                if not first:
                    out.write(',')
                else:
                    first = False
                out.write(l)

            out.write("]}")
        os.remove(geofilename)
        logging.info('%d geo features at %s' % (geo_count, user))
    else:
        classified_geofilename = None
        logging.info('No geo features at %s' % user)
    logging.info('Pulling tweets for %s...Done' % user)
    return classified_filename, classified_geofilename


def generate_pull_bucket(bucket, geobucket):
    b = _get_bucket(bucket)
    if bucket != geobucket:
        gb = _get_bucket(geobucket)
    elif geobucket:
        gb = b
    else:
        gb = None

    def func(input_line, is_geo_enabled):
        user, event, _, _, _ = _unpack(input_line)
        user = slugify(user)
        for status in ALL_STATUS:
            filename = _generate_filename(user, event, status)
            if _blob_exists(filename, b):
                return filename
        filename, geofilename = pull_user_timeline(input_line, bool(gb) and is_geo_enabled)
        _upload_file_gcloud(filename, b)
        if geofilename and gb:
            _upload_file_gcloud(geofilename, gb)
        return filename

    return func


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve timeline tweets for users.'
                                                 'Users are specified either on stdin or if filename is specified,'
                                                 ' then from the specified file')
    parser.add_argument('--filename', '-f', metavar='filename', type=str, nargs='?',
                        help='file with list of usernames')

    parser.add_argument('--kafka', '-k', metavar='kafka', type=str, nargs='?',
                        help='list of kafka servers to connect', default=os.environ.get('KAFKA_SERVERS', None))

    parser.add_argument('--kafka-topic', '-kt', metavar='kafka_topic', type=str, nargs='?',
                        help='kafka topic to connect to. default: tw_user',
                        default=os.environ.get('KAFKA_TOPIC', 'tw_users'))

    parser.add_argument('--bucket', '-b', metavar='bucket', type=str, nargs='?',
                        help='Google Cloud bucket name', default=os.environ.get('BUCKET_NAME', None))

    parser.add_argument('--geobucket', '-g', metavar='geobucket', type=str, nargs='?',
                        help='Google Cloud bucket name for geotagged features',
                        default=os.environ.get('GEOBUCKET_NAME', None))

    args = parser.parse_args()

    # We want to use a puller with upload if we have bucket info, but still make it work w/o bucket
    pull_function = pull_user_timeline

    if args.bucket:
        pull_function = generate_pull_bucket(args.bucket, args.geobucket)

    if args.filename:
        with open(args.filename, 'r') as f:
            for line in f:
                pull_function(line, True)
    elif args.kafka:
        topic = args.kafka_topic
        consumer = KafkaConsumer(topic, group_id='user_puller',
                                 bootstrap_servers=args.kafka,
                                 )

        for msg in consumer:
            if msg and msg.value:
                logging.info('User received from Kafka: %s' % msg.value)
                pull_function(msg.value, True)

    else:
        for msg in sys.stdin:
            if msg:
                pull_function(msg, True)

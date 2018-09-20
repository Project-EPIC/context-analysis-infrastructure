import json, argparse, sys, jsonlines, io, csv, os
import urllib.parse
import urllib.request
import numpy as np
import multiprocessing

CSV_ROWS = [
    'tweet_id',
    'user',
    'user id',
    'date',
    'text'
]

def load_results_file(file='test/results.json'):
    try:
        res = json.load(open(file,'r'))
        return res
    except:
        raise

def tweet_to_feature(tweet):
    #Handle geo/coordinate info
    geo = None
    if 'coordinates' in tweet:
        if tweet['coordinates']:
            geo = tweet['coordinates']
    else:
        if 'geo' in tweet:
            if tweet['geo']:
                geo = {'type':'Point',
                       'coordinates': reversed(tweet['geo']['coordinates'])}
    return {
        'type':'Feature',
        'properties':{
            'user':tweet['user']['screen_name'],
            'date':tweet['created_at'],
            'text':tweet['text'],
            'tweetID':tweet['id_str']
        },
        'geometry':geo
    }, geo

def tweet_to_csv(tweet):
    return [
        tweet['id_str'],
        tweet['user']['screen_name'],
        tweet['user']['id_str'],
        tweet['created_at'],
        tweet['text']
        ]

def process_user(user):
    features = []
    ids   = [];
    geoCount = 0;

    try:
        with open(output+'/csv/'+user['user']+'.csv','w') as user_csv_out:
            csvwriter = csv.writer(user_csv_out, delimiter=",",
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(CSV_ROWS)

            with open(output+'/jsonl/'+user['user']+'.jsonl','w') as user_jsonl_out:

                with urllib.request.urlopen(user['url']) as response:
                    fp = io.BytesIO( response.read() )
                    reader = jsonlines.Reader(fp)

                    for tweet in reader:

                        ids.append(tweet['id_str']) #Debugging

                        #Write json tweet as line delimited json
                        user_jsonl_out.write(json.dumps(tweet)+"\n")

                        #Write simple CSV
                        csvwriter.writerow(tweet_to_csv(tweet))

                        #Convert to geojson
                        tweet_feature, geo = tweet_to_feature(tweet)
                        if geo:
                            geoCount += 1;
                        features.append(tweet_feature)
                #Logging
                sys.stderr.write("{0}: {1} unique IDs and {2} geojson features, geo: {3}".format(user['user'],
                            len(np.unique(ids)),
                            len(features),
                            geoCount)+"\n")
    except:
        print("FAILURE ON: " + user['user'])
        raise

    try:
        if geoCount > 0:
            json.dump({'type':'FeatureCollection','features':features},
                open(output+'/geojson/'+user['user']+'.geojson','w'))
    except:
        print("Couldn't write geojson")
        raise

# Runtime
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download contextual stream files for users.')
    parser.add_argument('--filename', '-f', metavar='filename',
                                            type=str, nargs='?',
                                            help='json file with results array')
    parser.add_argument('--output', '-o', metavar='output',
                                        type=str, nargs='?',
                                        help='Output directory')
    parser.add_argument('--processors', '-P',   metavar='processors',
                                                type=int, nargs='?',
                                                help='Number of processors')
    args = parser.parse_args()

    processors = args.processors or multiprocessing.cpu_count()-2;
    output     = args.output or 'test/output'

    if args.filename:
        sys.stderr.write("Starting download with " + args.filename + " on {0} processors\n".format(processors))
        res = load_results_file(args.filename)

        sys.stderr.write("Found {0} files\n".format(len(res)))

        if not os.path.exists(output+'/jsonl'):
            os.makedirs(output+'/jsonl')
        if not os.path.exists(output+'/geojson'):
            os.makedirs(output+'/geojson')
        if not os.path.exists(output+'/csv'):
            os.makedirs(output+'/csv')

        p = multiprocessing.Pool(processors)

        p.map(process_user, res)

    else:
        print("")
        parser.print_help()

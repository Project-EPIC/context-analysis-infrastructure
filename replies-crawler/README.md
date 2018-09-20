# Twitter replies crawler

Twitter replies downloader. Prepared for a local usage and cloud.


## Development
Required: `python, pip, virtualenv`, [Google Cloud Access](https://googlecloudplatform.github.io/google-cloud-python/latest/core/auth.html)(optional) and [Twitter app credentials](https://apps.twitter.com/)

1. `virtualenv env`
2. `source env/bin/activate`
3. `pip install -r requirements.txt`
4. Set enviroment variables 

Highly recommended to use `virtualenv` to avoid conflicts with other packages in the system.

## Enviroment variables

Set the following using your application credentials.

- **ACCESS_TOKEN**: Twitter registered application access token
- **ACCESS_TOKEN_SECRET**: Twitter registered application access token secret
- **CONSUMER_KEY**: Twitter registered application consumer key
- **CONSUMER_SECRET**: Twitter registered application consumer secret
- **BUCKET_NAME**: Google Storage bucket name where tweets get stored in
- **GEOBUCKET_NAME**: Google Storage bucket name where geo located tweets get stored in


## Usage

To start pulling users we need to execute `python crawler.py`. The following are all the available inputs

### Stdin

We can input users by stdin. 1 user/line. This allows us to quicly retrieve data for 1 user like:
`echo "twitter" | python crawler.py`

### File

We can set a file as input by using the `-f` or `--filename` argument. 
For help please check `python crawler.py -h`.

### Kafka

We can set kafka as the source of username by using `-k` or `--kafka` argument with the kafka server.
In addition you can also set the topic to connect to with `-kt` or `--kafka-topic` argument.


## Possible outputs

### File

Output will always be stored in  the results folder locally. No config needed, this is default

### Google Cloud Bucket

We can set a destination bucket by using `-b` or `--bucket` argument or setting the **BUCKET** environment variable. 
Make sure to have the Google Cloud authentication prepared, follow 
[this](https://google-cloud-python.readthedocs.io/en/latest/core/auth.html) instructions to set it up.
Make sure you have write permissions for the specified bucket.


## Publishing docker image
Required: `docker`

1. `docker login`
2. `make push`

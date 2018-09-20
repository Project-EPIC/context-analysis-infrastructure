#  Results UI

Web UI that shows latest downloaded users classified by type (complete, incomplete...). 

## Development
Required: `python, pip, virtualenv` and [Google Cloud Access](https://googlecloudplatform.github.io/google-cloud-python/latest/core/auth.html) 

1. `virtualenv env`
2. `source env/bin/activate`
3. `pip install -r requirements.txt`
4. `python main.py`

Code auto-refresh is enabled by default.

## Environment variables

- **BUCKET_NAME**: Name of the bucket where data is stored. Default: `twitter-users-test`
- **PRODUCTION**: Enable production mode. This makes the app avoid showing verbose errors to users.

## Storage requirements

Files must comply with the following path: `/results/{eventname}/{status}/{username}.json` inside of the specified bucket.


## Publishing docker image
Required: `docker`

1. `docker login`
2. `make push`


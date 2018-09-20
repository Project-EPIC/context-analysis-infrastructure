# Requester UI

Web UI that allows analysts to submit new batches of users

## Development
Required: `python, pip, virtualenv` and Kafka running on localhost

1. `virtualenv env`
2. `source env/bin/activate`
3. `pip install -r requirements.txt`
4. `python main.py`

Code auto-refresh is enabled by default.

## Environment variables

- **KAFKA_SERVERS**: Kafka servers where to push the users. Default: `localhost`
- **KAFKA_TOPIC**: Topic where to post users. Default: `tw_users`
- **PRODUCTION**: Enable production mode. This makes the app avoid showing verbose errors to users.

## Message format

Messages sent to Kafka by this service are of the form:

```
{{username}},{{event_name}},{{start_date}},{{end_date}}
```

## Publishing docker image
Required: `docker`

1. `docker login`
2. `make push`

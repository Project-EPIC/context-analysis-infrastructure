# Kubernetes deployment - Contextual Query

Required: Kubernetes cluster configured into local `kubectl`

## Cluster requirements

We used Google Cloud managed Kubernetes Engine with 2 nodes of type: n1-standard-1 (1 vCPU, 3.75 GB memory).

It's is worth taking into consideration that Google Cloud offers grants for research projects. Read more [here](https://lp.google-mkto.com/gcp-research-credits.html).

## Set up
- Generate and download keyfile: https://cloud.google.com/storage/docs/authentication#generating-a-private-key
- `./create_secret_keyfile.sh`
- `cp twsecrets.yml.template twsecrets.yml`
- Fill twsecrets with Twitter app credentials
- `kubectl create -f ./kafka/`
- `kubectl create -f twsecrets.yml`
- `kubectl create -f twservers.yml`
- `kubectl create -f client_server.yml`


## Acces requester

Requirement: Have `kubectl` to access the cluster

- `kubectl proxy`
- `http://localhost:8001/api/v1/namespaces/default/services/requester:http/proxy/`

## Modify CORS for buckets

To allow files to be downloaded from webpages for online analysis, you will need to change the CORS setting in your Google Storage settings. Use the script in `gutil/set-cors-bucket.sh` to do that. You can change the bucket name in the same script.

# Context Analysis infrastructure

This repository is an aggregation of software components and Kubernetes deployments manifests. It includes everything needed to run the infrastructure described in Project EPIC's paper "Incorporating Context and Location Into Social Media Analysis:  A Scalable, Cloud-Based Approach for More Powerful Data Science".


## Deployment on Kubernetes

See [kubernetes-infrastructure/README.md](kubernetes-infrastructure/README.md)

## Creating docker images

Check out each folder's README to release a new image for each component. You may have to change the user in the Makefile so that DockerHub accepts your push. To use your custom image, change the docker image field in the Kubernetes deployment file.



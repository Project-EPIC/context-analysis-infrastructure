#!/usr/bin/env bash

kubectl create secret generic keyfile --from-file=keyfile.json=./keyfile.json
#!/bin/sh -eux
sudo apt-get install docker jq
network=$(docker inspect --format '{{json .NetworkSettings.Networks}}' `hostname` \
  | jq -r 'keys[0]')
docker pull -q amazon/dynamodb-local:latest
docker run \
  -v /home/runner/work/data:/home/dynamodblocal/data \
  -w "/home/dynamodblocal" \
  --name dynamodb \
  --network "$network" \
  --rm \
  -d \
  amazon/dynamodb-local:latest
sleep 10
docker ps
docker logs dynamodb

#!/bin/bash

FRONT_CONTAINER_NAME="front"
NGINX_CONTAINER_NAME="nginx"

docker events --filter 'event=restart' --filter 'event=start' --filter 'event=stop' --filter 'event=die' --format '{{.Type}} {{.Action}} {{.Actor.Attributes.name}}' |
while read event; do
    echo "Event received: $event"
    if [[ "$event" == *"$FRONT_CONTAINER_NAME"* ]]; then
        echo "Restarting $NGINX_CONTAINER_NAME container"
        docker restart $NGINX_CONTAINER_NAME
    fi
done
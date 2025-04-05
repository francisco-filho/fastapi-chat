#!/bin/bash

docker run --rm --env-file=./.env -e "OPENAI_API_KEY=$OPENAI_API_KEY" -p 8000:8000 --network=host fastapi-chat



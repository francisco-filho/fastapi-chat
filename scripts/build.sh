#!/bin/bash

VERSION=$(python scripts/get_version.py)
echo "- Build image fastapi-chat:$VERSION"

docker build -t fastapi-chat:$VERSION .

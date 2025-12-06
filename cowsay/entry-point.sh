#!/bin/sh

PORT=${1:-8080}

echo "Starting server on port $PORT..."

# Install dependencies
apk add --update nodejs npm && npm install

# Start server with the PORT env variable
PORT=$PORT npm start

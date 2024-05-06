# checkov server

Run checkov as webserver. Send base64 encoded tar.gz of your code to `/checkov` API endpoint to receive scan results. Also connect with TFC/E Run tasks via the `/tf_run_task_review` endpoint.

## Getting started

- Clone repo
	`git clone github.com/tmprender/checkov-utils.git`

- Build container image from this directory (/checkov-utils/server)
	`docker build -t checkov-utils/server .`

- Run container image locally or deploy
	`docker run -p 5000:5000 -d checkov-utils/server`

- Make API call
	```sh
	#!/bin/bash

	# Directory to be packaged and uploaded
	SOURCE_DIR="path/to/your/source_code_directory"

	# Archive the directory
	tar --exclude=".terraform*" --exclude=".git/*" -czvf archive.tar.gz $SOURCE_DIR

	# Encode the archive in base64
	openssl base64 -in archive.tar.gz -out encoded_archive.txt

	# Create a JSON payload with the base64-encoded content
	json_payload=$(jq -n --arg file "$(cat encoded_archive.txt)" '{"file": $file, "flags": []}')

	# Send the POST request
	curl -X POST localhost:5000/checkov \
		-H "Content-Type: application/json" \
		-d "$json_payload"

	# Clean up temporary files
	rm archive.tar.gz encoded_archive.txt


- Example with CLI args
	```sh
	json_payload=$(jq -n --arg file "$(cat encoded_archive.txt)" '{"file": $file, "flags":["--check", "CKV_SECRET_6"]}')

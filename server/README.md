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
	json_payload=$(jq -n --arg file "$(cat encoded_archive.txt)" '{"file": $file, "flags": []}')
	
	curl -X POST http://example.com/api_endpoint \
     		-H "Content-Type: application/json" \
     		-d "$json_payload"



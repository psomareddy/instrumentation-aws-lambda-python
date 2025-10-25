curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:us-east-1:254067382080:layer:splunk-apm:119 --query 'Content.Location' --output text) --output ./hello_world/layer.zip

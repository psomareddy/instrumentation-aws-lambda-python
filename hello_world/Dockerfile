FROM alpine:latest as layer-copy

ARG AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-"us-east-1"}
ARG AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ARG AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ARG AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}

RUN apk add aws-cli curl unzip

RUN mkdir -p /opt

# Manually run the script below to download layer.zip into the hello_world folder
# RUN curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:us-east-1:254067382080:layer:splunk-apm:119 --query 'Content.Location' --output text) --output layer.zip
COPY layer.zip ./
RUN unzip layer.zip -d /opt
RUN rm layer.zip

FROM public.ecr.aws/lambda/python:3.12
COPY --from=layer-copy /opt /opt

# Copy function code
COPY app.py requirements.txt ./

COPY collector.yaml /opt

RUN python3.12 -m pip install -r requirements.txt -t .

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]

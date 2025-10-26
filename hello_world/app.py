import json
import logging

import requests
from opentelemetry import trace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get a Tracer instance
tracer = trace.get_tracer(__name__)

def lambda_handler(event, context):
    logger.info(f'Calling out to my sample lamb handler v2')
    current_span = trace.get_current_span()
    current_span.set_attribute("r-version", "1.5.0")
    check_ip()
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }

@tracer.start_as_current_span("check_ip")
def check_ip():
    logger.info(f'Start executing check_ip method ')
    current_span = trace.get_current_span()
    try:
        ip = requests.get('http://checkip.amazonaws.com')
        current_span.set_attribute("ip.address", ip.text)
    except requests.exceptions.RequestException as e:
        logger.error(e)
        raise e
    logger.info(f'End executing check_ip method ')
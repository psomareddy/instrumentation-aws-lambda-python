import json
import logging

from opentelemetry import trace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get a Tracer instance
tracer = trace.get_tracer(__name__)

def lambda_handler(event, context):
    logger.info(f'Calling out to my sample lamb handler v2')
    do_work()
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }

@tracer.start_as_current_span("do_work")
def do_work():
    logger.info(f'Executing method do_work')
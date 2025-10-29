import json
import logging
import http.client
from collections.abc import Mapping
from typing import Optional, Dict

from opentelemetry import trace, baggage, context
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.trace import StatusCode, Status
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get a Tracer instance
tracer = trace.get_tracer(__name__)


class HttpRequestHandler:

    def __init__(self, url: str, method: str, headers: Mapping[str, str]):
        self.url = url
        self.method = method
        self.headers = headers
        # session_timeout_ms =
        self.enable_otel = True
        self.otel_child_span = True
        self.otel_inject_headers = True
        self.otel_span_attrs = dict([("system", "Inbound")])
        self.baggage_index_on_span = True
        self.baggage= dict([("tenant.id", "us-fintech"), ("org.id", "1234")])
        self.otel_span_name = "GET checkip.amazonaws.com"
        self.data ={"ip.address": "172.16.17.32"}


    # inject open telemetry propagation headers
    def _with_trace_headers(self, headers: Optional[dict]) -> dict:
        # carrier type must implement get(key) and set(key, value) methods. Dict does not implement carrierT, so use dict instead
        carrier = headers or dict()

        logging.info(f"_with_trace_headers: Headers before otel injection = {headers}")
        if self.enable_otel and self.otel_inject_headers:
            baggage_ctx : context = context.get_current()
            for (key, value) in self.baggage.items():
                baggage_ctx = baggage.set_baggage(key, value, baggage_ctx)
            W3CBaggagePropagator().inject(carrier, baggage_ctx)
            TraceContextTextMapPropagator().inject(carrier)
        return carrier

    def Send_http_request(self, connection: http.client.HTTPSConnection):
        # Create child span
        with tracer.start_as_current_span(self.otel_span_name, kind=trace.SpanKind.CLIENT) as span:
            logger.info(f"Send_http_request: Setting span attributes = {self.otel_span_attrs}")
            if self.otel_span_attrs:
                try:
                    for k, v in self.otel_span_attrs.items():
                        span.set_attribute(k, v)
                except Exception:
                    pass

            otel_headers = self._with_trace_headers(self.headers)
            logger.info(f"Send_http_request: Headers after otel injection={otel_headers}")

            logger.info(f"Invoking HTTP {self.method} request to {self.url} with headers={self.headers}")
            logger.info("HTTP method type is %s and its value is %s", type(self.method).__name__, self.method)
            logger.info("HTTP URL type is %s and its value is %s", type(self.url).__name__, self.url)
            logger.info("HTTP Header's type is %s and its value is %s", type(self.headers).__name__, self.headers)
            if self.method in ["POST", "PUT"] and self.data:
                connection.request(
                    method=self.method,
                    url=self.url,
                    body=self.data,
                    headers=self.headers
                )
            else:
                connection.request(
                    method=self.method,
                    url=self.url,
                    headers=self.headers
                )

def lambda_handler(event, context):
    logger.info(f'Calling out to my sample lambda handler v2')
    current_span = trace.get_current_span()
    current_span.set_attribute("r-version", "1.5.0")
    my_ip = check_ip()
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "ip.address": my_ip,
            }
        ),
    }

@tracer.start_as_current_span("check_ip")
def check_ip() -> str:
    logger.info(f'Start executing check_ip')
    my_ip = "unknown"
    current_span = trace.get_current_span()
    # current_span.set_attribute("ip.address", ip.text)
    try:
        # Create a connection to the server
        conn = http.client.HTTPSConnection("checkip.amazonaws.com:443")
        #TODO send multiple headers
        http_request_handler = HttpRequestHandler("/", "GET", {"termial": "delta"})
        logger.info(f'About to create request')
        http_request_handler.Send_http_request(conn)

        logger.info(f'About to read response')
        # Get the response
        response = conn.getresponse()

        # Print the response status and body
        logger.info(f'Status: {response.status}, reason: {response.reason}')
        logger.info(f'Headers: {response.getheaders()}', )
        body = response.read().decode()
        logger.info(f'Body: {body}')

        current_span.set_attribute("ip.address", body.strip())
        my_ip = body.strip()
    except http.client.HTTPException as e:
        logger.exception(f"HTTP Error: {e}")
    except ConnectionRefusedError:
        logger.exception("Connection refused. Ensure the server is running and accessible.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        current_span.set_status(Status(StatusCode.ERROR))
        current_span.record_exception(e)
    finally:
        # Close the connection
        if 'conn' in locals() and conn:
            conn.close()
    logger.info(f'End executing check_ip')
    return my_ip




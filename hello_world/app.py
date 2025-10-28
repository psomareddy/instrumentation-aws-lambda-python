import json
import logging
import http.client
from contextlib import contextmanager
from typing import Optional, Dict

#import requests
from opentelemetry import trace, baggage, context
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.trace import StatusCode, Status
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.propagate import inject as otel_inject

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get a Tracer instance
tracer = trace.get_tracer(__name__)


class HttpRequestHandler:

    def __init__(self, url, method, headers):
        self.url = url
        self.method = method
        self.headers = headers,
        # session_timeout_ms = ,
        self.enable_otel = True,
        self.otel_child_span = True,
        self.otel_inject_headers = True,
        self.otel_span_attrs = {"system": "Inbound"},
        self.baggage_index_on_span = True,
        self.baggage= {"tenant.id": "us-fintech"},
        self.otel_span_name = "GET checkip.amazonaws.com"


    @contextmanager
    def _maybe_child_span(self):
        # Create child span
        with tracer.start_as_current_span(self.otel_span_name, kind=trace.SpanKind.CLIENT) as span:
            # Set span attributes
            # if self.otel_span_attrs:
            #     try:
            #         for k, v in self.otel_span_attrs.items():
            #             span.set_attribute(k, v)
            #     except Exception:
            #         pass

            # Set baggage
            # if self.baggage:
            #     try:
            #         for k, v in self.baggage.items():
            #             if self.baggage_index_on_span:
            #                 span.set_attribute(k, v)
            #     except Exception:
            #         pass
            yield

    # inject open telemetry propagation headers
    def _with_trace_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        carrier: Dict[str, str] = dict(headers or {})
        if self.enable_otel and self.otel_inject_headers:
            context_with_baggage = context.get_current()
            # try:
            #     for k, v in self.baggage.items():
            #         logger.info(f"bag key is {k}={v}")
            #         context_with_baggage = baggage.set_baggage(k, v, context=context_with_baggage)
            # except Exception:
            #     pass
            otel_inject(carrier)
            W3CBaggagePropagator().inject(
                carrier,
                context=context_with_baggage
            )
        return carrier

    def Send_http_request(self, connection: http.client.HTTPSConnection):
        with self._maybe_child_span():
            self.headers = self._with_trace_headers(self.headers)
            logger.info(f"headers after Otel injection={self.headers}")
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

# @tracer.start_as_current_span("check_ip1")
# def check_ip1():
#     logger.info(f'Start executing check_ip method ')
#     current_span = trace.get_current_span()
#     try:
#         # Inject otel propagation headers,
#         headers = {}
#         ctx = baggage.set_baggage("hello", "world")
#         W3CBaggagePropagator().inject(headers, ctx)
#         TraceContextTextMapPropagator().inject(headers, ctx)
#         logger.info(f"Propagation headers: {headers}")
#
#         # Create a connection to the server
#         conn = http.client.HTTPSConnection("checkip.amazonaws.com:443")
#
#         # Send a GET request to the root path
#         conn.request("GET", "/", headers=headers)
#
#         # Get the response
#         response = conn.getresponse()
#
#         # Print the response status and body
#         logger.info(f'Status: {response.status}, reason: {response.reason}')
#         logger.info(f'Headers: {response.getheaders()}', )
#         body = response.read().decode()
#         logger.info(f'Body: {body}')
#
#         current_span.set_attribute("ip.address", body.strip())
#     except http.client.HTTPException as e:
#         logger.error(f"HTTP Error: {e}")
#         current_span.set_status(Status(StatusCode.ERROR))
#         current_span.record_exception(e)
#     except ConnectionRefusedError:
#         logger.error("Connection refused. Ensure the server is running and accessible.")
#         current_span.set_status(Status(StatusCode.ERROR))
#         current_span.record_exception(e)
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         current_span.set_status(Status(StatusCode.ERROR))
#         current_span.record_exception(e)
#     finally:
#         # Close the connection
#         if 'conn' in locals() and conn:
#             conn.close()
#     logger.info(f'End executing check_ip method ')

@tracer.start_as_current_span("check_ip")
def check_ip():
    logger.info(f'Start executing check_ip')
    current_span = trace.get_current_span()
    # current_span.set_attribute("ip.address", ip.text)
    try:
        # Create a connection to the server
        conn = http.client.HTTPSConnection("checkip.amazonaws.com:443")
        http_request_handler = HttpRequestHandler("/", "GET", {})
        http_request_handler.Send_http_request(conn)

        # Get the response
        response = conn.getresponse()

        # Print the response status and body
        logger.info(f'Status: {response.status}, reason: {response.reason}')
        logger.info(f'Headers: {response.getheaders()}', )
        body = response.read().decode()
        logger.info(f'Body: {body}')

        current_span.set_attribute("ip.address", body.strip())
    except http.client.HTTPException as e:
        logger.error(f"HTTP Error: {e}")
    except ConnectionRefusedError:
        logger.error("Connection refused. Ensure the server is running and accessible.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        current_span.set_status(Status(StatusCode.ERROR))
        current_span.record_exception(e)
    finally:
        # Close the connection
        if 'conn' in locals() and conn:
            conn.close()
    logger.info(f'End executing check_ip')




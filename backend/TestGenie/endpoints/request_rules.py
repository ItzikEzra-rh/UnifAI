from flask import request
from functools import reduce
from provider.lucid.lucid import metadata
import logging


class RequestRules:
    """ Set of "before_request/after_request" rules """
    PAYLOAD_SIZE_LIMIT = 10 * pow(100, 4)  # 1000MB=1GB

    def __init__(self, app):
        self.app = app
        self.metadata = metadata()
        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self):
        self.size_limit()

    def _after_request(self, response):
        """
        Invoke these methods after each request.
        Each method must accept a single argument 'response' and return a new/updated response object.

        :param response:
        :return:
        """
        fns = [self.set_metadata]
        return reduce(lambda prev, f: f(prev), fns, response)

    def size_limit(self):
        """ Limit content payload size to 1000MB for POST commands"""
        if request.method == "POST":
            content_length = int(request.content_length or 0)
            if content_length > self.PAYLOAD_SIZE_LIMIT:
                logging.info("Content length is too large: %s", content_length)
                raise Exception("Content length is too large")

    def set_metadata(self, response):
        """
        Return the BE PLATFORM in the headers.

        :param response:
        :return:
        """
        for key, data in self.metadata.items():
            response.headers[key] = data
        return response

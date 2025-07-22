import logging

import requests
from requests.exceptions import HTTPError, RequestException

requests_logger = logging.getLogger("requests_sender")
requests_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("requests.log")
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ),
)
requests_logger.addHandler(file_handler)
requests_logger.propagate = False


class RequestsSender:

    def request(self, **kwargs) -> str:
        url = kwargs.get("url")
        method = kwargs.get("method", "GET")
        logging.debug("Req %s url:%s", method, url)
        try:
            res = requests.request(**kwargs)
            res.raise_for_status()
        except HTTPError as error:
            requests_logger.error(
                "Error: status=%s, method=%s, url=%s, error=%s, text=%s",
                res.status_code,
                method,
                url,
                str(error),
                res.text,
            )
            raise error
        except RequestException as error:
            requests_logger.error(
                "Error: method=%s, url=%s, error=%s",
                method,
                url,
                str(error),
            )
            raise error
        else:
            requests_logger.info(
                "Request: method=%s, url=%s, status_code=%s",
                method,
                url,
                res.status_code,
            )
            return res.text
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseRequestHandler(ABC):
    """
    Abstract base class for handling HTTP requests using the requests library.
    Provides common functionality for request handling, retries, error handling
    and session management that can be extended by concrete implementation classes.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
    ):
        """
        Initialize the base request handler with common configuration.

        Args:
            base_url: Optional base URL to prepend to all request paths
            timeout: Default request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
            headers: Default headers to include in all requests
            verify_ssl: Enable/disable SSL certificate verification
        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers or {}
        self.verify_ssl = verify_ssl
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure a requests Session instance."""
        session = requests.Session()
        if self.headers:
            session.headers.update(self.headers)
        return session

    def _build_url(self, path: str) -> str:
        """Build full URL from base URL and request path."""
        if self.base_url:
            return f"{self.base_url}/{path.lstrip('/')}"
        return path

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """
        Execute HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path or full URL
            **kwargs: Additional arguments passed to requests.request

        Returns:
            Response object from requests library

        Raises:
            RequestException: If request fails after all retries
        """
        url = self._build_url(path)
        attempt = 0

        while attempt <= self.max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=kwargs.pop("timeout", self.timeout),
                    verify=self.verify_ssl,
                    **kwargs,
                )

                # Check for HTTP errors
                response.raise_for_status()

                logger.debug(
                    f"Request succeeded: {method} {url} Status: {response.status_code}"
                )
                return response

            except RequestException as e:
                attempt += 1
                logger.warning(
                    f"Request failed (attempt {attempt}/{self.max_retries + 1}): {method} {url} Error: {str(e)}"
                )

                if attempt <= self.max_retries:
                    time.sleep(self.retry_delay * attempt)  # Exponential backoff
                else:
                    logger.error(
                        f"Request failed permanently after {self.max_retries + 1} attempts: {method} {url}"
                    )
                    raise

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        """Convenience method for GET requests."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        """Convenience method for POST requests."""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        """Convenience method for PUT requests."""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        """Convenience method for DELETE requests."""
        return self.request("DELETE", path, **kwargs)

    @abstractmethod
    def authenticate(self) -> None:
        """
        Abstract method to handle authentication.
        Must be implemented by concrete classes.
        Should update session headers or cookies with authentication credentials.
        """
        pass

    @abstractmethod
    def handle_rate_limit(self, response: requests.Response) -> None:
        """
        Abstract method to handle rate limiting responses.
        Must be implemented by concrete classes.

        Args:
            response: Response object that triggered the rate limit (HTTP 429)
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up session."""
        self.session.close()
        logger.debug("Request session closed")

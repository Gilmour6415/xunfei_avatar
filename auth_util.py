import base64
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse
import pytz


class AuthUtil:
    @staticmethod
    def assemble_request_url(
        request_url: str, api_key: str, api_secret: str, method: str = "GET"
    ) -> str:
        """Assemble request URL with authentication parameters

        Args:
            request_url: The original request URL
            api_key: API key for authentication
            api_secret: API secret for signing
            method: HTTP method (default: GET)

        Returns:
            The signed request URL with authentication parameters
        """
        try:
            # Convert WebSocket URL to HTTP(S)
            http_request_url = request_url.replace("ws://", "http://").replace(
                "wss://", "https://"
            )
            url = urlparse(http_request_url)

            # Get UTC formatted date
            date = datetime.now(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
            host = url.hostname

            # Build signature string
            path = url.path if url.path else "/"
            builder = f"host: {host}\ndate: {date}\n{method} {path} HTTP/1.1"

            # Generate HMAC SHA-256 signature
            digest = hmac.new(
                api_secret.encode("utf-8"), builder.encode("utf-8"), hashlib.sha256
            ).digest()
            sha = base64.b64encode(digest).decode("utf-8")

            # Build authorization header
            authorization = f'hmac username="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{sha}"'
            auth_base = base64.b64encode(authorization.encode("utf-8")).decode("utf-8")

            # URL encode parameters and build final URL
            return (
                f"{request_url}?authorization={urllib.parse.quote(auth_base)}"
                f"&host={urllib.parse.quote(host)}"
                f"&date={urllib.parse.quote(date)}"
            )
        except Exception as e:
            raise RuntimeError(f"assemble requestUrl error: {str(e)}")

    @staticmethod
    def assemble_request_header(
        request_url: str,
        api_key: str,
        api_secret: str,
        method: str,
        body: Optional[bytes] = None,
    ) -> Dict[str, str]:
        """Assemble request headers with authentication

        Args:
            request_url: The request URL
            api_key: API key for authentication
            api_secret: API secret for signing
            method: HTTP method
            body: Request body (optional)

        Returns:
            Dictionary containing all required headers
        """
        try:
            url = urlparse(request_url)
            # Get UTC formatted date
            date = datetime.now(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

            # Calculate body digest (SHA256)
            digest = ""
            if body:
                sha256 = hashlib.sha256(body).digest()
                digest = f"SHA-256={base64.b64encode(sha256).decode('utf-8')}"

            host = url.hostname
            if url.port:
                host = f"{host}:{url.port}"

            path = url.path if url.path else "/"

            # Build signature string
            builder = (
                f"host: {host}\n"
                f"date: {date}\n"
                f"{method} {path} HTTP/1.1\n"
                f"digest: {digest}"
            )

            # Generate HMAC SHA-256 signature
            signature = hmac.new(
                api_secret.encode("utf-8"), builder.encode("utf-8"), hashlib.sha256
            ).digest()
            sha = base64.b64encode(signature).decode("utf-8")

            # Build authorization header
            authorization = (
                f'hmac-auth api_key="{api_key}", algorithm="hmac-sha256", '
                f'headers="host date request-line digest", signature="{sha}"'
            )

            # Prepare headers
            headers = {"authorization": authorization, "host": host, "date": date}
            if digest:
                headers["digest"] = digest

            return headers
        except Exception as e:
            raise RuntimeError(f"assemble requestHeader error: {str(e)}")

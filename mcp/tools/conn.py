###
# Copyright (2023) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

"""
CMF API Connection module.

Low-level HTTP transport layer for communicating with CMF Server.
Handles session management, retries, and connection pooling.

Originally from the cmfAPI package (https://github.com/atripathy86/cmfapi).
Inlined here to remove the external dependency.
"""

import requests
import urllib3
import warnings
import logging
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger("cmf-mcp.conn")


class cmfConnection:
    def __init__(self, base_url, max_retries=3, retry_delay=1,
                 connection_timeout=10, disable_connection_pooling=False, tls_verify=None):
        """
        Initialize the CMF API connection.

        :param base_url: CMF Server base URL
        :param max_retries: Maximum number of retry attempts for failed requests
        :param retry_delay: Base delay in seconds between retries (exponential backoff)
        :param connection_timeout: Connection timeout in seconds
        :param disable_connection_pooling: If True, disable connection pooling
        :param tls_verify: TLS certificate verification. Can be:
                          - None (default): Read from CMF_TLS_VERIFY env var, defaults to False
                          - True: Verify certificates using system CA bundle
                          - False: Disable verification (default for HTTP-based CMF servers)
                          - str: Path to custom CA bundle file
        """
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = connection_timeout
        self.disable_connection_pooling = disable_connection_pooling
        
        # Configure TLS verification (default: disabled for HTTP-based CMF servers)
        if tls_verify is None:
            env_verify = os.getenv("CMF_TLS_VERIFY", "false").lower()
            if env_verify in ("false", "0", "no", "disabled"):
                self.tls_verify = False
            elif env_verify in ("true", "1", "yes", "enabled"):
                self.tls_verify = True
            else:
                # Treat as path to CA bundle
                self.tls_verify = env_verify
        else:
            self.tls_verify = tls_verify
        
        # Only suppress warnings when TLS verification is explicitly disabled
        if self.tls_verify is False:
            logger.warning("TLS certificate verification is DISABLED. This is insecure and not recommended for production.")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            warnings.simplefilter("ignore", category=urllib3.exceptions.InsecureRequestWarning)
        else:
            verify_msg = f"path: {self.tls_verify}" if isinstance(self.tls_verify, str) else "system CA bundle"
            logger.info(f"TLS certificate verification ENABLED using {verify_msg}")

        # Create a session for connection reuse
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )

        # Configure adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1 if disable_connection_pooling else 10,
            pool_maxsize=1 if disable_connection_pooling else 10
        )

        # Mount the adapter to both HTTP and HTTPS
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set timeout
        self.session.timeout = connection_timeout

    def _do_call(self, method, endpoint, params=None, data=None, files=None, is_binary=False):
        """Internal method to send a request to the CMF API."""
        url = f"{self.base_url}{endpoint}"
        headers = None

        # Convert dictionary to form-encoded string if sending multipart
        request_data = None if files else data
        form_data = data if files else None

        try:
            logger.debug(f"Sending {method} request to {url}")
            response = self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=request_data,
                files=files,
                data=form_data,
                verify=self.tls_verify,
                timeout=self.connection_timeout
            )

            # Handle 4xx responses gracefully
            if 400 <= response.status_code < 500:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    return {"error": f"HTTP {response.status_code}: {response.reason}"}

            response.raise_for_status()

            if is_binary:
                return response.content

            if not response.content.strip():
                return {}

            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                return response.text

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            raise Exception(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out: {str(e)}")
            raise Exception(f"Request timed out: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Request error: {str(e)}")

    def get(self, endpoint, params=None, is_binary=False):
        """Send a GET request."""
        return self._do_call("GET", endpoint, params=params, is_binary=is_binary)

    def post(self, endpoint, data=None, files=None):
        """Send a POST request."""
        return self._do_call("POST", endpoint, data=data, files=files)

    def put(self, endpoint, data=None):
        """Send a PUT request."""
        return self._do_call("PUT", endpoint, data=data)

    def delete(self, endpoint, params=None, data=None):
        """Send a DELETE request."""
        return self._do_call("DELETE", endpoint, params=params, data=data)

    def patch(self, endpoint, data=None):
        """Send a PATCH request."""
        return self._do_call("PATCH", endpoint, data=data)

    def exit(self):
        """Close the session and release connections."""
        self.session.close()

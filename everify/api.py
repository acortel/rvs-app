import requests
import jwt
import time
import logging
from typing import Optional
import webbrowser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EVerifyClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str = 'https://ws.everify.gov.ph/api'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[int] = None

    def is_token_expired(self) -> bool:
        if self.token_expiry is None:
            return True
        current_time = int(time.time())
        return current_time >= self.token_expiry

    def refresh_token(self) -> Optional[str]:
        try:
            response = requests.post(
                f'{self.base_url}/auth',
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["data"]["access_token"]
                decoded = jwt.decode(self.access_token, options={"verify_signature": False})
                self.token_expiry = int(decoded["exp"])
                logger.info(f"Token refreshed successfully. Expires at: {self.token_expiry}")
                return self.access_token
            else:
                logger.error(f"Token refresh failed. Status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None

    def get_access_token(self) -> Optional[str]:
        if self.is_token_expired():
            return self.refresh_token()
        return self.access_token

    def verify_person(self, payload: dict) -> dict:
        token = self.get_access_token()
        if not token:
            return {"error": "Authentication failed."}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            response = requests.post(f"{self.base_url}/query", headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def verify_qr(self, payload: dict) -> dict:
        token = self.get_access_token()
        if not token:
            return {"error": "Authentication failed."}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            response = requests.post(f"{self.base_url}/query/qr", headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def check_qr(self, payload: dict) -> dict:
        token = self.get_access_token()
        if not token:
            return {"error": "Authentication failed."}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            response = requests.post(f"{self.base_url}/query/qr/check", headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def is_liveness_server_available(self, liveness_result_url: str = None) -> bool:
        """Check if the liveness server is running and accessible."""
        url = liveness_result_url or "http://127.0.0.1:5000/liveness_result"
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False

    def start_liveness_check(self, liveness_url: str = None):
        """Start liveness check by opening browser. Returns URL or None if server unavailable."""
        url = liveness_url or "http://127.0.0.1:5000/liveness"
        try:
            webbrowser.open(url)
            return url
        except Exception as e:
            print(f"Failed to open liveness URL: {e}")
            return None

    def get_liveness_result(self, liveness_result_url: str = None) -> dict:
        url = liveness_result_url or "http://127.0.0.1:5000/liveness_result"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}", "data": response.text}
        except Exception as e:
            return {"error": str(e)}

    def post_liveness_result(self, session_id: str, liveness_result_url: str = None) -> dict:
        url = liveness_result_url or "http://127.0.0.1:5000/liveness_result"
        try:
            response = requests.post(url, json={"face_liveness_session_id": session_id})
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}", "data": response.text}
        except Exception as e:
            return {"error": str(e)}

    def delete_liveness_result(self, liveness_result_url: str = None) -> dict:
        url = liveness_result_url or "http://127.0.0.1:5000/liveness_result"
        try:
            response = requests.delete(url)
            if response.status_code in (200, 204):
                return {"message": "Liveness session ID cleared"}
            else:
                return {"error": f"Status {response.status_code}", "data": response.text}
        except Exception as e:
            return {"error": str(e)}
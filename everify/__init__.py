"""
eVerify Python SDK
A modular package for integrating eVerify functionality into Python applications.
"""

from .api import EVerifyClient
from .db import EVerifyDB
from .config import get_config
from .utils import download_image

__version__ = "1.0.0"
__all__ = ["EVerifyClient", "EVerifyDB", "get_config", "download_image"] 
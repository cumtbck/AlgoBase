"""
API Module

Provides REST API and WebSocket interfaces for the CLAUDE application.
"""

from .server import app

__all__ = ["app"]
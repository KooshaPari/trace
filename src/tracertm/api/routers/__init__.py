"""API routers for TraceRTM.

This module re-exports all routers for convenient import.
Each router should be imported from this module to avoid circular imports.
"""

from tracertm.api.routers.accounts import router as accounts
from tracertm.api.routers.adrs import router as adrs
from tracertm.api.routers.agent import router as agent
from tracertm.api.routers.analysis import router as analysis
from tracertm.api.routers.auth import router as auth
from tracertm.api.routers.blockchain import router as blockchain
from tracertm.api.routers.contracts import router as contracts
from tracertm.api.routers.errors import router as errors
from tracertm.api.routers.execution import router as execution
from tracertm.api.routers.features import router as features
from tracertm.api.routers.github import router as github
from tracertm.api.routers.health import router as health
from tracertm.api.routers.health_canary import router as health_canary
from tracertm.api.routers.integrations import router as integrations
from tracertm.api.routers.item_specs import router as item_specs
from tracertm.api.routers.items import router as items
from tracertm.api.routers.links import router as links
from tracertm.api.routers.mcp import router as mcp
from tracertm.api.routers.notifications import router as notifications
from tracertm.api.routers.oauth import router as oauth
from tracertm.api.routers.quality import router as quality
from tracertm.api.routers.specifications import router as specifications
from tracertm.api.routers.system import router as system
from tracertm.api.routers.websocket import router as websocket
from tracertm.api.routers.workflows import router as workflows

__all__ = [
    "accounts",
    "adrs",
    "agent",
    "analysis",
    "auth",
    "blockchain",
    "contracts",
    "errors",
    "execution",
    "features",
    "github",
    "health",
    "health_canary",
    "integrations",
    "item_specs",
    "items",
    "links",
    "mcp",
    "notifications",
    "oauth",
    "quality",
    "specifications",
    "system",
    "websocket",
    "workflows",
]

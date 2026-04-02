"""Analytics endpoints for item specs.

This module combines all analytics sub-routers:
- EARS & Quality analysis
- Version chain and Merkle proofs
- Test flakiness analysis
- Defect classification (ODC/CVSS)
- Impact analysis and prioritization
- Coverage gaps and suspect links

For implementation details, see the individual router modules.
"""

from fastapi import APIRouter

from tracertm.api.routers.item_specs_analytics_defect import router as defect_router
from tracertm.api.routers.item_specs_analytics_ears_quality import (
    router as ears_quality_router,
)
from tracertm.api.routers.item_specs_analytics_flakiness import (
    router as flakiness_router,
)
from tracertm.api.routers.item_specs_analytics_gaps import router as gaps_router
from tracertm.api.routers.item_specs_analytics_impact import (
    router as impact_router,
)
from tracertm.api.routers.item_specs_analytics_version import (
    router as version_router,
)

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics"])

router.include_router(ears_quality_router)
router.include_router(version_router)
router.include_router(flakiness_router)
router.include_router(defect_router)
router.include_router(impact_router)
router.include_router(gaps_router)

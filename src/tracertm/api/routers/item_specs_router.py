"""API Router for enhanced Item specifications.

This module is the main entry point that combines all item spec sub-routers:
- Requirements
- Tests
- Epics
- User Stories
- Tasks
- Defects
- Statistics
- Analytics

For implementation details, see the individual router modules.
"""

from fastapi import APIRouter

from tracertm.api.routers.item_specs_analytics import router as analytics_router
from tracertm.api.routers.item_specs_defects import router as defects_router
from tracertm.api.routers.item_specs_epics import router as epics_router
from tracertm.api.routers.item_specs_requirements import router as requirements_router
from tracertm.api.routers.item_specs_stats import router as stats_router
from tracertm.api.routers.item_specs_stories import router as stories_router
from tracertm.api.routers.item_specs_tasks import router as tasks_router
from tracertm.api.routers.item_specs_tests import router as tests_router

router = APIRouter(
    prefix="/item-specs",
    tags=["Item Specifications"],
)

router.include_router(requirements_router)
router.include_router(tests_router)
router.include_router(epics_router)
router.include_router(stories_router)
router.include_router(tasks_router)
router.include_router(defects_router)
router.include_router(stats_router)
router.include_router(analytics_router)

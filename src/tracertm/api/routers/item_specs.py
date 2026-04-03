"""API Router for enhanced Item specifications.

This module provides the main router that combines all item spec sub-routers.
For implementation details, see the individual router modules in this directory:
- item_specs_router.py - Main router that combines all sub-routers
- item_specs_schemas.py - Pydantic models
- item_specs_requirements.py - Requirement endpoints
- item_specs_tests.py - Test endpoints
- item_specs_epics.py - Epic endpoints
- item_specs_stories.py - User story endpoints
- item_specs_tasks.py - Task endpoints
- item_specs_defects.py - Defect endpoints
- item_specs_stats.py - Statistics endpoints
- item_specs_analytics.py - Analytics endpoints
"""

from tracertm.api.routers.item_specs_router import router

__all__ = ["router"]

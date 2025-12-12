from __future__ import annotations
import logging
from ams.ams_enums import AssetType
from ams.ams_paths import PROJECT_ROOT
from ams.asset import Asset
from core import uuid_utils
from core.logging_utils import get_logger

LOGGER = get_logger(name=__name__, level=logging.INFO)


def create_asset(name: str, asset_type: AssetType, tags: list[str] | None = None,
) -> Asset:
    """Create an asset with a unique uuid."""
    asset = Asset(
        name=name,
        asset_type=asset_type,
        uuid=uuid_utils.generate_uuid(),
        tags=tags,
    )
    if asset.source_dir.exists():
        LOGGER.info(f"Asset '{asset.name}' already exists: {asset.source_dir.relative_to(PROJECT_ROOT)}")
    else:
        asset.init_metadata()


if __name__ == "__main__":
    create_asset(name="staveley_court", asset_type=AssetType.environment)

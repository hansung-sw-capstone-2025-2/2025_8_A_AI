from typing import List, Optional
import json

from src.core.database import Database
from src.domain.models import Cohort


class LibraryRepository:
    async def get_by_id(self, library_id: int) -> Optional[Cohort]:
        row = await Database.fetchrow("""
            SELECT library_id, library_name, panel_ids, created_date
            FROM library
            WHERE library_id = $1
        """, library_id)

        if not row:
            return None

        panel_ids = row['panel_ids']
        if isinstance(panel_ids, str):
            panel_ids = json.loads(panel_ids)

        return Cohort(
            cohort_id=str(row['library_id']),
            cohort_name=row['library_name'],
            panel_count=len(panel_ids) if panel_ids else 0,
            panel_ids=panel_ids or [],
            created_at=str(row['created_date']) if row.get('created_date') else None
        )

    async def get_panel_ids(self, library_id: int) -> List[str]:
        row = await Database.fetchrow("""
            SELECT panel_ids FROM library WHERE library_id = $1
        """, library_id)

        if not row or not row['panel_ids']:
            return []

        panel_ids = row['panel_ids']
        if isinstance(panel_ids, str):
            panel_ids = json.loads(panel_ids)

        if not isinstance(panel_ids, list):
            panel_ids = list(panel_ids) if panel_ids else []

        return panel_ids

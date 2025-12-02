from typing import List, Optional
from datetime import datetime
import json

from src.core.database import Database
from src.domain.models import SearchHistory


class SearchHistoryRepository:
    async def create(
        self,
        member_id: Optional[int],
        content: str,
        panel_ids: List[str],
        concordance_rates: List[float]
    ) -> int:
        result = await Database.fetchrow("""
            INSERT INTO search_history (member_id, content, panel_ids, concordance_rate, date)
            VALUES ($1, $2, $3, $4::double precision[], $5)
            RETURNING id
        """, member_id, content, panel_ids, concordance_rates, datetime.now().date())

        return result['id'] if result else 0

    async def get_by_id(self, search_id: int) -> Optional[SearchHistory]:
        row = await Database.fetchrow("""
            SELECT id, member_id, content, panel_ids, concordance_rate, created_date
            FROM search_history
            WHERE id = $1
        """, search_id)

        if not row:
            return None

        panel_ids = row['panel_ids'] or []
        if isinstance(panel_ids, str):
            panel_ids = json.loads(panel_ids)

        return SearchHistory(
            id=row['id'],
            member_id=row.get('member_id'),
            content=row['content'] or '',
            panel_ids=panel_ids,
            concordance_rate=row.get('concordance_rate') or [],
            date=row.get('created_date')
        )

    async def get_by_member(self, member_id: int, limit: int = 20) -> List[SearchHistory]:
        rows = await Database.fetch("""
            SELECT id, member_id, content, panel_ids, concordance_rate, created_date
            FROM search_history
            WHERE member_id = $1
            ORDER BY created_date DESC
            LIMIT $2
        """, member_id, limit)

        histories = []
        for row in rows:
            panel_ids = row['panel_ids'] or []
            if isinstance(panel_ids, str):
                panel_ids = json.loads(panel_ids)

            histories.append(SearchHistory(
                id=row['id'],
                member_id=row.get('member_id'),
                content=row['content'] or '',
                panel_ids=panel_ids,
                concordance_rate=row.get('concordance_rate') or [],
                date=row.get('created_date')
            ))

        return histories

    async def get_recent_queries(self, member_id: int, limit: int = 10) -> List[str]:
        rows = await Database.fetch("""
            SELECT content FROM search_history
            WHERE member_id = $1 AND content IS NOT NULL AND content != ''
            ORDER BY created_date DESC
            LIMIT $2
        """, member_id, limit)

        return [row['content'] for row in rows]

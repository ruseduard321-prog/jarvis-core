from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from backend.core.domain_exceptions import DatabaseUnavailableError, RepositoryError, ResourceNotFoundError
from backend.mappers.agent_mapper import AgentMapper
from backend.models.agent import Agent
from backend.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AgentRepository(BaseRepository[Agent]):
    """Repository for persistent agent entities stored in Supabase."""

    TABLE_NAME = "agents"

    @staticmethod
    def _load_core_business_agents() -> list[dict[str, object]]:
        seed_file = Path(__file__).resolve().parents[1] / "seeds" / "core_business_agents.json"
        with seed_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise RepositoryError()
        return [item for item in data if isinstance(item, dict)]

    async def list_agents(self, owner_user_id: str | None = None, active_only: bool = True) -> list[Agent]:
        if not await self.database.health_check():
            raise DatabaseUnavailableError()

        try:
            client = getattr(self.database, "client", None)
            if client is None:
                raise DatabaseUnavailableError()

            query = client.table(self.TABLE_NAME).select("*").order("created_at", desc=False)
            if owner_user_id:
                query = query.eq("owner_user_id", owner_user_id)
            if active_only:
                query = query.eq("is_active", True)

            response = query.execute()
            rows = getattr(response, "data", None) or []
            return [AgentMapper.from_row(row) for row in rows]
        except DatabaseUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Error listing agents")
            raise RepositoryError() from exc

    async def get_agent(self, agent_id: str) -> Agent:
        if not await self.database.health_check():
            raise DatabaseUnavailableError()

        try:
            client = getattr(self.database, "client", None)
            if client is None:
                raise DatabaseUnavailableError()

            response = client.table(self.TABLE_NAME).select("*").eq("id", agent_id).limit(1).execute()
            rows = getattr(response, "data", None) or []
            if not rows:
                raise ResourceNotFoundError(f"Agent not found: {agent_id}")
            return AgentMapper.from_row(rows[0])
        except ResourceNotFoundError:
            raise
        except DatabaseUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Error getting agent")
            raise RepositoryError() from exc

    async def create_agent(
        self,
        owner_user_id: str,
        slug: str,
        name: str,
        mission: str,
        allowed_delegations: list[str] | None = None,
    ) -> Agent:
        if not await self.database.health_check():
            raise DatabaseUnavailableError()

        try:
            client = getattr(self.database, "client", None)
            if client is None:
                raise DatabaseUnavailableError()

            payload = {
                "owner_user_id": owner_user_id,
                "slug": slug,
                "name": name,
                "mission": mission,
                "is_active": True,
            }
            response = client.table(self.TABLE_NAME).insert(payload).select("*").execute()
            rows = getattr(response, "data", None) or []
            if not rows:
                raise RepositoryError()
            return AgentMapper.from_row(rows[0])
        except DatabaseUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Error creating agent")
            raise RepositoryError() from exc

    async def update_agent(
        self,
        agent_id: str,
        slug: str | None = None,
        name: str | None = None,
        mission: str | None = None,
        allowed_delegations: list[str] | None = None,
        is_active: bool | None = None,
    ) -> Agent:
        if not await self.database.health_check():
            raise DatabaseUnavailableError()

        try:
            client = getattr(self.database, "client", None)
            if client is None:
                raise DatabaseUnavailableError()

            update_payload: dict[str, object] = {"updated_at": datetime.utcnow().isoformat()}
            if slug is not None:
                update_payload["slug"] = slug
            if name is not None:
                update_payload["name"] = name
            if mission is not None:
                update_payload["mission"] = mission
            if is_active is not None:
                update_payload["is_active"] = is_active

            response = (
                client.table(self.TABLE_NAME)
                .update(update_payload)
                .eq("id", agent_id)
                .select("*")
                .execute()
            )
            rows = getattr(response, "data", None) or []
            if not rows:
                raise ResourceNotFoundError(f"Agent not found: {agent_id}")
            return AgentMapper.from_row(rows[0])
        except ResourceNotFoundError:
            raise
        except DatabaseUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Error updating agent")
            raise RepositoryError() from exc

    async def seed_core_business_agents(self, owner_user_id: str = "system") -> list[Agent]:
        """Ensure core business agents exist without runtime-specific logic."""
        if not await self.database.health_check():
            raise DatabaseUnavailableError()

        try:
            client = getattr(self.database, "client", None)
            if client is None:
                raise DatabaseUnavailableError()

            seeded: list[Agent] = []
            for agent_seed in self._load_core_business_agents():
                existing_response = (
                    client.table(self.TABLE_NAME)
                    .select("*")
                    .eq("owner_user_id", owner_user_id)
                    .eq("slug", agent_seed["slug"])
                    .limit(1)
                    .execute()
                )
                existing_rows = getattr(existing_response, "data", None) or []
                if existing_rows:
                    updated_response = (
                        client.table(self.TABLE_NAME)
                        .update(
                            {
                                "slug": agent_seed["slug"],
                                "name": agent_seed["name"],
                                "mission": agent_seed["mission"],
                                "is_active": True,
                                "updated_at": datetime.utcnow().isoformat(),
                            }
                        )
                        .eq("id", existing_rows[0]["id"])
                        .select("*")
                        .execute()
                    )
                    updated_rows = getattr(updated_response, "data", None) or []
                    if not updated_rows:
                        raise RepositoryError()
                    seeded.append(AgentMapper.from_row(updated_rows[0]))
                    continue

                create_response = (
                    client.table(self.TABLE_NAME)
                    .insert(
                        {
                            "owner_user_id": owner_user_id,
                            "slug": agent_seed["slug"],
                            "name": agent_seed["name"],
                            "mission": agent_seed["mission"],
                            "is_active": True,
                        }
                    )
                    .select("*")
                    .execute()
                )
                create_rows = getattr(create_response, "data", None) or []
                if not create_rows:
                    raise RepositoryError()
                seeded.append(AgentMapper.from_row(create_rows[0]))

            return seeded
        except DatabaseUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Error seeding core business agents")
            raise RepositoryError() from exc

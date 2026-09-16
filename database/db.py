"""
Database layer for AI Orchestrator.
SQLite with async support for state management.
"""

import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

DB_PATH = Path("data/orchestrator.db")


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Connect to database and create tables."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        if self.db:
            await self.db.close()

    async def _create_tables(self):
        await self.db.executescript("""
            -- Generation history
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                service TEXT NOT NULL,
                request_type TEXT NOT NULL,
                prompt TEXT,
                parameters TEXT,
                result TEXT,
                status TEXT DEFAULT 'pending',
                tokens_used INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                latency_ms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            -- User profiles and preferences
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                preferred_language TEXT DEFAULT 'en',
                preferred_style TEXT,
                api_key_hash TEXT,
                total_generations INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP
            );

            -- User feedback for learning
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                generation_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generation_id) REFERENCES generations(id)
            );

            -- API keys and auth
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT,
                rate_limit INTEGER DEFAULT 100,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            -- Service health history
            CREATE TABLE IF NOT EXISTS service_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms INTEGER,
                error_message TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Analytics events
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id TEXT,
                service TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Plugin registry
            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT,
                service_type TEXT NOT NULL,
                config TEXT,
                is_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );

            -- Cache for frequent requests
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                service TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                response TEXT NOT NULL,
                expires_at TIMESTAMP,
                hit_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_generations_user ON generations(user_id);
            CREATE INDEX IF NOT EXISTS idx_generations_service ON generations(service);
            CREATE INDEX IF NOT EXISTS idx_generations_created ON generations(created_at);
            CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
            CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type);
            CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics(created_at);
            CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key);
        """)
        await self.db.commit()

    # --- Generation CRUD ---

    async def create_generation(self, user_id: str, service: str, request_type: str,
                                 prompt: str, parameters: dict = None) -> int:
        cursor = await self.db.execute(
            """INSERT INTO generations (user_id, service, request_type, prompt, parameters)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, service, request_type, prompt, json.dumps(parameters or {}))
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_generation(self, gen_id: int, status: str = None, result: str = None,
                                 tokens_used: int = None, cost_usd: float = None,
                                 latency_ms: int = None):
        updates = []
        values = []
        if status:
            updates.append("status = ?")
            values.append(status)
        if result:
            updates.append("result = ?")
            values.append(result)
        if tokens_used is not None:
            updates.append("tokens_used = ?")
            values.append(tokens_used)
        if cost_usd is not None:
            updates.append("cost_usd = ?")
            values.append(cost_usd)
        if latency_ms is not None:
            updates.append("latency_ms = ?")
            values.append(latency_ms)
        if status in ("completed", "failed"):
            updates.append("completed_at = CURRENT_TIMESTAMP")

        values.append(gen_id)
        await self.db.execute(
            f"UPDATE generations SET {', '.join(updates)} WHERE id = ?",
            values
        )
        await self.db.commit()

    async def get_generation(self, gen_id: int) -> Optional[dict]:
        async with self.db.execute("SELECT * FROM generations WHERE id = ?", (gen_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_user_generations(self, user_id: str, limit: int = 50) -> List[dict]:
        async with self.db.execute(
            "SELECT * FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    # --- User Management ---

    async def upsert_user(self, user_id: str, **kwargs) -> None:
        fields = list(kwargs.keys())
        values = list(kwargs.values())
        if fields:
            await self.db.execute(
                f"""INSERT INTO users (id, {', '.join(fields)})
                    VALUES (?, {', '.join(['?' for _ in fields])})
                    ON CONFLICT(id) DO UPDATE SET
                    last_active = CURRENT_TIMESTAMP""",
                [user_id] + values
            )
        else:
            await self.db.execute(
                """INSERT OR IGNORE INTO users (id) VALUES (?)
                   ON CONFLICT(id) DO UPDATE SET last_active = CURRENT_TIMESTAMP""",
                (user_id,)
            )
        await self.db.commit()

    async def get_user(self, user_id: str) -> Optional[dict]:
        async with self.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_user_stats(self, user_id: str, tokens: int, cost: float):
        await self.db.execute(
            """UPDATE users SET
                total_generations = total_generations + 1,
                total_tokens = total_tokens + ?,
                total_cost_usd = total_cost_usd + ?,
                last_active = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (tokens, cost, user_id)
        )
        await self.db.commit()

    # --- Feedback ---

    async def add_feedback(self, user_id: str, generation_id: int, rating: int,
                            comment: str = None, tags: str = None) -> int:
        cursor = await self.db.execute(
            "INSERT INTO feedback (user_id, generation_id, rating, comment, tags) VALUES (?, ?, ?, ?, ?)",
            (user_id, generation_id, rating, comment, tags)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def get_feedback_stats(self, user_id: str = None) -> dict:
        where = "WHERE user_id = ?" if user_id else ""
        params = (user_id,) if user_id else ()
        async with self.db.execute(
            f"SELECT AVG(rating) as avg_rating, COUNT(*) as total FROM feedback {where}", params
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {"avg_rating": 0, "total": 0}

    # --- Analytics ---

    async def log_event(self, event_type: str, user_id: str = None,
                         service: str = None, metadata: dict = None):
        await self.db.execute(
            "INSERT INTO analytics (event_type, user_id, service, metadata) VALUES (?, ?, ?, ?)",
            (event_type, user_id, service, json.dumps(metadata or {}))
        )
        await self.db.commit()

    async def get_analytics(self, event_type: str = None, user_id: str = None,
                             days: int = 30) -> List[dict]:
        query = "SELECT * FROM analytics WHERE created_at >= datetime('now', ?)"
        params = [f"-{days} days"]
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        query += " ORDER BY created_at DESC"

        async with self.db.execute(query, params) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    # --- Service Health ---

    async def log_health(self, service: str, status: str, latency_ms: int = None,
                          error_message: str = None):
        await self.db.execute(
            "INSERT INTO service_health (service, status, latency_ms, error_message) VALUES (?, ?, ?, ?)",
            (service, status, latency_ms, error_message)
        )
        await self.db.commit()

    async def get_service_health(self, service: str, hours: int = 24) -> List[dict]:
        async with self.db.execute(
            """SELECT * FROM service_health
               WHERE service = ? AND checked_at >= datetime('now', ?)
               ORDER BY checked_at DESC""",
            (service, f"-{hours} hours")
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    # --- Cache ---

    async def get_cache(self, cache_key: str) -> Optional[dict]:
        async with self.db.execute(
            "SELECT * FROM cache WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP",
            (cache_key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await self.db.execute(
                    "UPDATE cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
                    (cache_key,)
                )
                await self.db.commit()
                return dict(row)
        return None

    async def set_cache(self, cache_key: str, service: str, request_hash: str,
                         response: str, ttl_seconds: int = 3600):
        await self.db.execute(
            """INSERT OR REPLACE INTO cache (cache_key, service, request_hash, response, expires_at)
               VALUES (?, ?, ?, ?, datetime('now', ?))""",
            (cache_key, service, request_hash, response, f"+{ttl_seconds} seconds")
        )
        await self.db.commit()

    # --- Plugin Registry ---

    async def register_plugin(self, plugin_id: str, name: str, service_type: str,
                               version: str = None, config: dict = None):
        await self.db.execute(
            """INSERT OR REPLACE INTO plugins (id, name, service_type, version, config, updated_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (plugin_id, name, service_type, version, json.dumps(config or {}))
        )
        await self.db.commit()

    async def get_plugins(self, service_type: str = None) -> List[dict]:
        query = "SELECT * FROM plugins WHERE is_enabled = 1"
        params = []
        if service_type:
            query += " AND service_type = ?"
            params.append(service_type)
        async with self.db.execute(query, params) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    # --- Dashboard Stats ---

    async def get_dashboard_stats(self, user_id: str = None) -> dict:
        stats = {}

        # Total generations
        where = "WHERE user_id = ?" if user_id else ""
        params = (user_id,) if user_id else ()
        async with self.db.execute(f"SELECT COUNT(*) as count FROM generations {where}", params) as cursor:
            row = await cursor.fetchone()
            stats["total_generations"] = row["count"]

        # Total cost
        async with self.db.execute(f"SELECT SUM(cost_usd) as total FROM generations {where}", params) as cursor:
            row = await cursor.fetchone()
            stats["total_cost_usd"] = row["total"] or 0

        # Average latency
        async with self.db.execute(f"SELECT AVG(latency_ms) as avg FROM generations {where}", params) as cursor:
            row = await cursor.fetchone()
            stats["avg_latency_ms"] = row["avg"] or 0

        # Service breakdown
        async with self.db.execute(
            f"SELECT service, COUNT(*) as count, SUM(cost_usd) as cost FROM generations {where} GROUP BY service",
            params
        ) as cursor:
            stats["by_service"] = [dict(row) for row in await cursor.fetchall()]

        return stats


# Global database instance
db = Database()


async def get_db():
    """Dependency for FastAPI."""
    return db

import logging
import os
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


class Database:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not set")
        if "sslmode=" not in self.database_url:
            self.database_url = f"{self.database_url}?sslmode=require"

    def get_connection(self):
        try:
            return psycopg2.connect(
                self.database_url, cursor_factory=psycopg2.extras.DictCursor
            )
        except psycopg2.Error as exc:
            logger.exception("Failed to connect to PostgreSQL")
            raise exc

    def create_tables(self) -> None:
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date TEXT,
                gender TEXT,
                location TEXT,
                phone TEXT,
                pinfl TEXT,
                language TEXT DEFAULT 'en',
                registration_complete BOOLEAN DEFAULT TRUE,
                consent_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_at TIMESTAMPTZ",
            """
            CREATE TABLE IF NOT EXISTS hackathons (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                prize_pool TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stages (
                id SERIAL PRIMARY KEY,
                hackathon_id INT REFERENCES hackathons(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stage_reminders (
                id SERIAL PRIMARY KEY,
                stage_id INT REFERENCES stages(id) ON DELETE CASCADE,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                days_left INT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(stage_id, user_id, days_left)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS teams (
                id SERIAL PRIMARY KEY,
                hackathon_id INT REFERENCES hackathons(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                leader_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                field TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS team_members (
                id SERIAL PRIMARY KEY,
                team_id INT REFERENCES teams(id) ON DELETE CASCADE,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                role TEXT,
                portfolio TEXT,
                is_lead BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(team_id, user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id SERIAL PRIMARY KEY,
                stage_id INT REFERENCES stages(id) ON DELETE CASCADE,
                team_id INT REFERENCES teams(id) ON DELETE CASCADE,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                link TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(stage_id, team_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_teams_hackathon_id ON teams(hackathon_id)",
            "CREATE INDEX IF NOT EXISTS idx_stages_hackathon_id ON stages(hackathon_id)",
            "CREATE INDEX IF NOT EXISTS idx_submissions_stage_id ON submissions(stage_id)",
            "CREATE INDEX IF NOT EXISTS idx_submissions_team_id ON submissions(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id)",
        ]
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for query in queries:
                    cur.execute(query)
            conn.commit()

    def create_user(self, payload: Dict[str, Any]) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (
                        telegram_id, username, first_name, last_name, birth_date, gender,
                        location, phone, pinfl, registration_complete, consent_at
                    )
                    VALUES (%(telegram_id)s, %(username)s, %(first_name)s, %(last_name)s,
                            %(birth_date)s, %(gender)s, %(location)s, %(phone)s, %(pinfl)s, TRUE, %(consent_at)s)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        birth_date = EXCLUDED.birth_date,
                        gender = EXCLUDED.gender,
                        location = EXCLUDED.location,
                        phone = EXCLUDED.phone,
                        pinfl = EXCLUDED.pinfl,
                        registration_complete = TRUE,
                        consent_at = EXCLUDED.consent_at
                    """,
                    payload,
                )
            conn.commit()

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def update_user_language(self, telegram_id: int, language: str) -> None:
        self.update_user_field(telegram_id, "language", language)

    def update_user_field(self, telegram_id: int, field: str, value: str) -> None:
        if field not in {"first_name", "last_name", "birth_date", "gender", "location", "language"}:
            raise ValueError("Invalid field")
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {field} = %s WHERE telegram_id = %s",
                    (value, telegram_id),
                )
            conn.commit()

    def get_active_hackathons(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM hackathons WHERE is_active = TRUE ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]

    def get_hackathon(self, hackathon_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM hackathons WHERE id = %s", (hackathon_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def create_stage(
        self,
        hackathon_id: int,
        name: str,
        description: Optional[str],
        deadline: Optional[str],
        is_active: bool = True,
    ) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stages (hackathon_id, name, description, deadline, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (hackathon_id, name, description, deadline, is_active),
                )
                stage_id = cur.fetchone()[0]
            conn.commit()
        return stage_id

    def list_stages_for_hackathon(self, hackathon_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM stages WHERE hackathon_id = %s ORDER BY created_at DESC",
                    (hackathon_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def get_stage(self, stage_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM stages WHERE id = %s", (stage_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def set_stage_active(self, stage_id: int, is_active: bool) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE stages SET is_active = %s WHERE id = %s", (is_active, stage_id))
            conn.commit()

    def get_active_stages(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM stages WHERE is_active = TRUE")
                return [dict(row) for row in cur.fetchall()]

    def create_submission(self, stage_id: int, team_id: int, user_id: int, link: str) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO submissions (stage_id, team_id, user_id, link)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (stage_id, team_id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        link = EXCLUDED.link,
                        created_at = NOW()
                    RETURNING id
                    """,
                    (stage_id, team_id, user_id, link),
                )
                submission_id = cur.fetchone()[0]
            conn.commit()
        return submission_id

    def get_team_submission_for_stage(self, stage_id: int, team_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM submissions WHERE stage_id = %s AND team_id = %s",
                    (stage_id, team_id),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_stage_submissions(self, stage_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.*, t.name AS team_name
                    FROM submissions s
                    JOIN teams t ON s.team_id = t.id
                    WHERE s.stage_id = %s
                    ORDER BY s.created_at DESC
                    """,
                    (stage_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def record_stage_reminder(self, stage_id: int, user_id: int, days_left: int) -> bool:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stage_reminders (stage_id, user_id, days_left)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (stage_id, user_id, days_left) DO NOTHING
                    """,
                    (stage_id, user_id, days_left),
                )
                inserted = cur.rowcount == 1
            conn.commit()
        return inserted

    def create_hackathon(
        self,
        name: str,
        description: Optional[str],
        deadline: Optional[str],
        prize_pool: Optional[str],
        is_active: bool = True,
    ) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hackathons (name, description, deadline, prize_pool, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, description, deadline, prize_pool, is_active),
                )
                hackathon_id = cur.fetchone()[0]
            conn.commit()
        return hackathon_id

    def list_hackathons(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM hackathons ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]

    def set_hackathon_active(self, hackathon_id: int, is_active: bool) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE hackathons SET is_active = %s WHERE id = %s",
                    (is_active, hackathon_id),
                )
            conn.commit()

    def create_team(
        self,
        hackathon_id: int,
        name: str,
        code: str,
        leader_id: int,
        field: Optional[str],
    ) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO teams (hackathon_id, name, code, leader_id, field)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (hackathon_id, name, code, leader_id, field),
                )
                team_id = cur.fetchone()[0]
            conn.commit()
        return team_id

    def get_team(self, team_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM teams WHERE id = %s", (team_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def get_team_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM teams WHERE code = %s", (code,))
                row = cur.fetchone()
                return dict(row) if row else None

    def get_team_members(self, team_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tm.*, u.first_name || ' ' || u.last_name AS user_name
                    FROM team_members tm
                    JOIN users u ON u.telegram_id = tm.user_id
                    WHERE tm.team_id = %s
                    ORDER BY tm.joined_at
                    """,
                    (team_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def get_user_teams(self, user_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT h.name AS hackathon_name, t.name AS team_name, t.code
                    FROM team_members tm
                    JOIN teams t ON tm.team_id = t.id
                    JOIN hackathons h ON t.hackathon_id = h.id
                    WHERE tm.user_id = %s
                    ORDER BY t.created_at DESC
                    """,
                    (user_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def get_user_team_for_hackathon(self, user_id: int, hackathon_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.*
                    FROM team_members tm
                    JOIN teams t ON tm.team_id = t.id
                    WHERE tm.user_id = %s AND t.hackathon_id = %s
                    """,
                    (user_id, hackathon_id),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def add_team_member(
        self,
        team_id: int,
        user_id: int,
        role: Optional[str],
        portfolio: Optional[str],
        is_lead: bool,
    ) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO team_members (team_id, user_id, role, portfolio, is_lead)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (team_id, user_id, role, portfolio, is_lead),
                    )
                except psycopg2.errors.UniqueViolation as exc:
                    conn.rollback()
                    raise ValueError("User already in team") from exc
            conn.commit()

    def remove_team_member(self, team_id: int, user_id: int) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM team_members WHERE team_id = %s AND user_id = %s", (team_id, user_id))
            conn.commit()

    def update_team_leader(self, team_id: int, leader_id: int) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE teams SET leader_id = %s WHERE id = %s", (leader_id, team_id))
                cur.execute(
                    "UPDATE team_members SET is_lead = (user_id = %s) WHERE team_id = %s",
                    (leader_id, team_id),
                )
            conn.commit()

    def remove_team(self, team_id: int) -> None:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM teams WHERE id = %s", (team_id,))
            conn.commit()

    def get_hackathon_participants(self, hackathon_id: int) -> List[int]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT tm.user_id
                    FROM team_members tm
                    JOIN teams t ON tm.team_id = t.id
                    WHERE t.hackathon_id = %s
                    """,
                    (hackathon_id,),
                )
                return [row[0] for row in cur.fetchall()]

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]

    def get_all_teams(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.*, h.name AS hackathon_name
                    FROM teams t
                    JOIN hackathons h ON t.hackathon_id = h.id
                    ORDER BY t.created_at DESC
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def get_all_team_members(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tm.*, t.name AS team_name, u.first_name || ' ' || u.last_name AS user_name
                    FROM team_members tm
                    JOIN teams t ON tm.team_id = t.id
                    JOIN users u ON tm.user_id = u.telegram_id
                    ORDER BY tm.joined_at DESC
                    """
                )
                return [dict(row) for row in cur.fetchall()]

"""
Database module for ITCom Hackathons Bot
Supports PostgreSQL (production) and SQLite (development)
"""

import asyncio
import os
import random
import string
from datetime import datetime
from typing import Optional, List, Dict, Any

import asyncpg
import aiosqlite

# Check if we're using PostgreSQL or SQLite
DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_POSTGRES = DATABASE_URL.startswith('postgres')


def generate_team_code(length: int = 6) -> str:
    """Generate a random team code"""
    return ''.join(random.choices(string.digits, k=length))


class Database:
    def __init__(self):
        self.pool = None
        self.sqlite_path = 'hackathon_bot.db'
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if self._initialized:
            return
        
        if USE_POSTGRES:
            await self._init_postgres()
        else:
            await self._init_sqlite()
        
        self._initialized = True
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        
        async with self.pool.acquire() as conn:
            # Create tables
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    birth_date DATE,
                    phone VARCHAR(50),
                    pinfl VARCHAR(20),
                    gender VARCHAR(20),
                    location VARCHAR(255),
                    language VARCHAR(5) DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS hackathons (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    start_date DATE,
                    end_date DATE,
                    prize_pool VARCHAR(100),
                    image_url TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id SERIAL PRIMARY KEY,
                    hackathon_id INTEGER REFERENCES hackathons(id),
                    name VARCHAR(255) NOT NULL,
                    code VARCHAR(10) UNIQUE NOT NULL,
                    leader_id BIGINT REFERENCES users(user_id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS team_members (
                    id SERIAL PRIMARY KEY,
                    team_id INTEGER REFERENCES teams(id),
                    user_id BIGINT REFERENCES users(user_id),
                    role VARCHAR(100) DEFAULT 'Member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(team_id, user_id)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    hackathon_id INTEGER REFERENCES hackathons(id),
                    team_id INTEGER REFERENCES teams(id),
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, hackathon_id)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS stages (
                    id SERIAL PRIMARY KEY,
                    hackathon_id INTEGER REFERENCES hackathons(id),
                    number INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    task_description TEXT,
                    start_date DATE,
                    end_date DATE,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    stage_id INTEGER REFERENCES stages(id),
                    team_id INTEGER REFERENCES teams(id),
                    link TEXT,
                    notes TEXT,
                    submission_type VARCHAR(50) DEFAULT 'link',
                    file_name VARCHAR(255),
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    score DECIMAL(5,2),
                    UNIQUE(user_id, stage_id)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id SERIAL PRIMARY KEY,
                    hackathon_id INTEGER REFERENCES hackathons(id),
                    title VARCHAR(255),
                    content TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    async def _init_sqlite(self):
        """Initialize SQLite database"""
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    birth_date TEXT,
                    phone TEXT,
                    pinfl TEXT,
                    gender TEXT,
                    location TEXT,
                    language TEXT DEFAULT 'en',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS hackathons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    prize_pool TEXT,
                    image_url TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hackathon_id INTEGER,
                    name TEXT NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    leader_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hackathon_id) REFERENCES hackathons(id),
                    FOREIGN KEY (leader_id) REFERENCES users(user_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS team_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id INTEGER,
                    user_id INTEGER,
                    role TEXT DEFAULT 'Member',
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (team_id) REFERENCES teams(id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(team_id, user_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    hackathon_id INTEGER,
                    team_id INTEGER,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (hackathon_id) REFERENCES hackathons(id),
                    FOREIGN KEY (team_id) REFERENCES teams(id),
                    UNIQUE(user_id, hackathon_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hackathon_id INTEGER,
                    number INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    task_description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    is_active INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hackathon_id) REFERENCES hackathons(id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stage_id INTEGER,
                    team_id INTEGER,
                    link TEXT,
                    notes TEXT,
                    submission_type TEXT DEFAULT 'link',
                    file_name TEXT,
                    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    score REAL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (stage_id) REFERENCES stages(id),
                    FOREIGN KEY (team_id) REFERENCES teams(id),
                    UNIQUE(user_id, stage_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hackathon_id INTEGER,
                    title TEXT,
                    content TEXT NOT NULL,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hackathon_id) REFERENCES hackathons(id)
                )
            ''')
            
            await db.commit()
    
    # ============== USER METHODS ==============
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM users WHERE user_id = $1', user_id
                )
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM users WHERE user_id = ?', (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def create_user(self, user_id: int, username: str, first_name: str,
                         last_name: str, birth_date: str, phone: str, pinfl: str) -> Dict[str, Any]:
        """Create a new user"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, birth_date, phone, pinfl)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = $2, first_name = $3, last_name = $4,
                        birth_date = $5, phone = $6, pinfl = $7, updated_at = CURRENT_TIMESTAMP
                ''', user_id, username, first_name, last_name, birth_date, phone, pinfl)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, birth_date, phone, pinfl)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, birth_date, phone, pinfl))
                await db.commit()
        
        return await self.get_user(user_id)
    
    async def update_user_language(self, user_id: int, language: str) -> None:
        """Update user's language preference"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE users SET language = $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2',
                    language, user_id
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    'UPDATE users SET language = ? WHERE user_id = ?',
                    (language, user_id)
                )
                await db.commit()
    
    async def update_user_field(self, user_id: int, field: str, value: str) -> None:
        """Update a specific user field"""
        await self._ensure_initialized()
        
        allowed_fields = ['first_name', 'last_name', 'birth_date', 'gender', 'location']
        if field not in allowed_fields:
            raise ValueError(f"Field {field} is not allowed to be updated")
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f'UPDATE users SET {field} = $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2',
                    value, user_id
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    f'UPDATE users SET {field} = ? WHERE user_id = ?',
                    (value, user_id)
                )
                await db.commit()
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM users')
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('SELECT * FROM users') as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def count_users(self) -> int:
        """Count total users"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM users')
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                    row = await cursor.fetchone()
                    return row[0]
    
    # ============== HACKATHON METHODS ==============
    
    async def get_hackathon(self, hackathon_id: int) -> Optional[Dict[str, Any]]:
        """Get hackathon by ID"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM hackathons WHERE id = $1', hackathon_id
                )
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM hackathons WHERE id = ?', (hackathon_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def get_active_hackathons(self) -> List[Dict[str, Any]]:
        """Get all active hackathons"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM hackathons WHERE is_active = TRUE ORDER BY start_date'
                )
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM hackathons WHERE is_active = 1 ORDER BY start_date'
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def get_all_hackathons(self) -> List[Dict[str, Any]]:
        """Get all hackathons"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM hackathons ORDER BY created_at DESC')
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('SELECT * FROM hackathons ORDER BY created_at DESC') as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def create_hackathon(self, name: str, description: str, start_date: str,
                               end_date: str, prize_pool: str = None, image_url: str = None) -> Dict[str, Any]:
        """Create a new hackathon"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO hackathons (name, description, start_date, end_date, prize_pool, image_url)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                ''', name, description, start_date, end_date, prize_pool, image_url)
                return dict(row)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute('''
                    INSERT INTO hackathons (name, description, start_date, end_date, prize_pool, image_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, description, start_date, end_date, prize_pool, image_url))
                await db.commit()
                return await self.get_hackathon(cursor.lastrowid)
    
    async def update_hackathon(self, hackathon_id: int, **kwargs) -> None:
        """Update hackathon fields"""
        await self._ensure_initialized()
        
        allowed_fields = ['name', 'description', 'start_date', 'end_date', 'prize_pool', 'image_url', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return
        
        if USE_POSTGRES:
            set_clause = ', '.join(f'{k} = ${i+2}' for i, k in enumerate(updates.keys()))
            values = [hackathon_id] + list(updates.values())
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f'UPDATE hackathons SET {set_clause} WHERE id = $1',
                    *values
                )
        else:
            set_clause = ', '.join(f'{k} = ?' for k in updates.keys())
            values = list(updates.values()) + [hackathon_id]
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    f'UPDATE hackathons SET {set_clause} WHERE id = ?',
                    values
                )
                await db.commit()
    
    # ============== TEAM METHODS ==============
    
    async def get_team(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Get team by ID"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM teams WHERE id = $1', team_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('SELECT * FROM teams WHERE id = ?', (team_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def get_team_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get team by code"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM teams WHERE code = $1', code)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('SELECT * FROM teams WHERE code = ?', (code,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def create_team(self, hackathon_id: int, name: str, leader_id: int) -> Dict[str, Any]:
        """Create a new team"""
        await self._ensure_initialized()
        
        # Generate unique code
        code = generate_team_code()
        while await self.get_team_by_code(code):
            code = generate_team_code()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO teams (hackathon_id, name, code, leader_id)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                ''', hackathon_id, name, code, leader_id)
                team = dict(row)
                
                # Add leader as team member
                await conn.execute('''
                    INSERT INTO team_members (team_id, user_id, role)
                    VALUES ($1, $2, $3)
                ''', team['id'], leader_id, 'Team Lead')
                
                return team
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute('''
                    INSERT INTO teams (hackathon_id, name, code, leader_id)
                    VALUES (?, ?, ?, ?)
                ''', (hackathon_id, name, code, leader_id))
                team_id = cursor.lastrowid
                
                # Add leader as team member
                await db.execute('''
                    INSERT INTO team_members (team_id, user_id, role)
                    VALUES (?, ?, ?)
                ''', (team_id, leader_id, 'Team Lead'))
                
                await db.commit()
                return await self.get_team(team_id)
    
    async def add_team_member(self, team_id: int, user_id: int, role: str = 'Member') -> None:
        """Add a member to a team"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO team_members (team_id, user_id, role)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (team_id, user_id) DO NOTHING
                ''', team_id, user_id, role)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute('''
                    INSERT OR IGNORE INTO team_members (team_id, user_id, role)
                    VALUES (?, ?, ?)
                ''', (team_id, user_id, role))
                await db.commit()
    
    async def remove_team_member(self, team_id: int, user_id: int) -> None:
        """Remove a member from a team"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'DELETE FROM team_members WHERE team_id = $1 AND user_id = $2',
                    team_id, user_id
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    'DELETE FROM team_members WHERE team_id = ? AND user_id = ?',
                    (team_id, user_id)
                )
                await db.commit()
    
    async def get_team_members(self, team_id: int) -> List[Dict[str, Any]]:
        """Get all members of a team"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM team_members WHERE team_id = $1', team_id
                )
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM team_members WHERE team_id = ?', (team_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def count_teams(self, hackathon_id: int) -> int:
        """Count teams in a hackathon"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    'SELECT COUNT(*) FROM teams WHERE hackathon_id = $1', hackathon_id
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                async with db.execute(
                    'SELECT COUNT(*) FROM teams WHERE hackathon_id = ?', (hackathon_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0]
    
    async def count_all_teams(self) -> int:
        """Count all teams"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM teams')
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                async with db.execute('SELECT COUNT(*) FROM teams') as cursor:
                    row = await cursor.fetchone()
                    return row[0]
    
    # ============== REGISTRATION METHODS ==============
    
    async def register_user_for_hackathon(self, user_id: int, hackathon_id: int, team_id: int) -> None:
        """Register a user for a hackathon"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO registrations (user_id, hackathon_id, team_id)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, hackathon_id) DO UPDATE SET team_id = $3
                ''', user_id, hackathon_id, team_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO registrations (user_id, hackathon_id, team_id)
                    VALUES (?, ?, ?)
                ''', (user_id, hackathon_id, team_id))
                await db.commit()
    
    async def get_user_hackathon_registration(self, user_id: int, hackathon_id: int) -> Optional[Dict[str, Any]]:
        """Get user's registration for a specific hackathon"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT * FROM registrations 
                    WHERE user_id = $1 AND hackathon_id = $2
                ''', user_id, hackathon_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('''
                    SELECT * FROM registrations 
                    WHERE user_id = ? AND hackathon_id = ?
                ''', (user_id, hackathon_id)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def get_user_registrations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all hackathon registrations for a user"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM registrations WHERE user_id = $1', user_id
                )
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM registrations WHERE user_id = ?', (user_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def get_hackathon_participants(self, hackathon_id: int) -> List[Dict[str, Any]]:
        """Get all participants of a hackathon"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT u.* FROM users u
                    JOIN registrations r ON u.user_id = r.user_id
                    WHERE r.hackathon_id = $1
                ''', hackathon_id)
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('''
                    SELECT u.* FROM users u
                    JOIN registrations r ON u.user_id = r.user_id
                    WHERE r.hackathon_id = ?
                ''', (hackathon_id,)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    # ============== STAGE METHODS ==============
    
    async def get_stage(self, stage_id: int) -> Optional[Dict[str, Any]]:
        """Get stage by ID"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM stages WHERE id = $1', stage_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('SELECT * FROM stages WHERE id = ?', (stage_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def get_hackathon_stages(self, hackathon_id: int) -> List[Dict[str, Any]]:
        """Get all stages for a hackathon"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM stages WHERE hackathon_id = $1 ORDER BY number', hackathon_id
                )
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM stages WHERE hackathon_id = ? ORDER BY number', (hackathon_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def create_stage(self, hackathon_id: int, number: int, name: str,
                          task_description: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Create a new stage"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO stages (hackathon_id, number, name, task_description, start_date, end_date)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                ''', hackathon_id, number, name, task_description, start_date, end_date)
                return dict(row)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute('''
                    INSERT INTO stages (hackathon_id, number, name, task_description, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (hackathon_id, number, name, task_description, start_date, end_date))
                await db.commit()
                return await self.get_stage(cursor.lastrowid)
    
    async def update_stage_active(self, stage_id: int, is_active: bool) -> None:
        """Update stage active status"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE stages SET is_active = $1 WHERE id = $2',
                    is_active, stage_id
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    'UPDATE stages SET is_active = ? WHERE id = ?',
                    (1 if is_active else 0, stage_id)
                )
                await db.commit()
    
    # ============== SUBMISSION METHODS ==============
    
    async def get_submission(self, user_id: int, stage_id: int) -> Optional[Dict[str, Any]]:
        """Get user's submission for a stage"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT * FROM submissions 
                    WHERE user_id = $1 AND stage_id = $2
                ''', user_id, stage_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('''
                    SELECT * FROM submissions 
                    WHERE user_id = ? AND stage_id = ?
                ''', (user_id, stage_id)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def create_submission(self, user_id: int, stage_id: int, link: str, 
                               notes: str = None, submission_type: str = 'link',
                               file_name: str = None) -> Dict[str, Any]:
        """Create a new submission"""
        await self._ensure_initialized()
        
        # Get user's team
        stage = await self.get_stage(stage_id)
        registration = await self.get_user_hackathon_registration(user_id, stage['hackathon_id'])
        team_id = registration['team_id'] if registration else None
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO submissions (user_id, stage_id, team_id, link, notes, submission_type, file_name)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id, stage_id) DO UPDATE SET 
                        link = $4, notes = $5, submission_type = $6, file_name = $7
                    RETURNING *
                ''', user_id, stage_id, team_id, link, notes, submission_type, file_name)
                return dict(row)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO submissions (user_id, stage_id, team_id, link, notes, submission_type, file_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, stage_id, team_id, link, notes, submission_type, file_name))
                await db.commit()
                return await self.get_submission(user_id, stage_id)
    
    async def remove_registration(self, user_id: int, hackathon_id: int) -> None:
        """Remove user's hackathon registration"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'DELETE FROM registrations WHERE user_id = $1 AND hackathon_id = $2',
                    user_id, hackathon_id
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    'DELETE FROM registrations WHERE user_id = ? AND hackathon_id = ?',
                    (user_id, hackathon_id)
                )
                await db.commit()
    
    async def get_stage_submissions(self, stage_id: int) -> List[Dict[str, Any]]:
        """Get all submissions for a stage"""
        await self._ensure_initialized()
        
        if USE_POSTGRES:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM submissions WHERE stage_id = $1', stage_id
                )
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    'SELECT * FROM submissions WHERE stage_id = ?', (stage_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

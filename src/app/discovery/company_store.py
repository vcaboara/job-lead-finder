"""SQLite storage for discovered companies and jobs."""

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from app.discovery.base_provider import Company, CompanySize, IndustryType

logger = logging.getLogger(__name__)


class CompanyStore:
    """SQLite-based storage for companies and jobs.
    
    Example:
        store = CompanyStore("companies.db")
        store.initialize()
        
        # Save a company
        company_id = store.save_company(company)
        
        # Find companies
        companies = store.find_companies(
            industries=[IndustryType.TECH],
            sizes=[CompanySize.STARTUP]
        )
    """

    def __init__(self, db_path: str | Path = "data/companies.db"):
        """Initialize store with database path."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        """Create database schema."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    website TEXT NOT NULL UNIQUE,
                    careers_url TEXT,
                    industry TEXT NOT NULL,
                    size TEXT NOT NULL,
                    description TEXT,
                    tech_stack TEXT,
                    locations TEXT,
                    funding_stage TEXT,
                    discovered_via TEXT NOT NULL,
                    discovered_at TEXT NOT NULL,
                    last_checked TEXT,
                    active INTEGER DEFAULT 1,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    description TEXT,
                    location TEXT,
                    posted_date TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    active INTEGER DEFAULT 1,
                    metadata TEXT,
                    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS discovery_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    companies_found INTEGER DEFAULT 0,
                    companies_new INTEGER DEFAULT 0,
                    companies_updated INTEGER DEFAULT 0,
                    errors TEXT,
                    metadata TEXT,
                    duration_seconds REAL
                );
                
                CREATE TABLE IF NOT EXISTS custom_industries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    keywords TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
                CREATE INDEX IF NOT EXISTS idx_companies_size ON companies(size);
                CREATE INDEX IF NOT EXISTS idx_companies_active ON companies(active);
                CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active);
            """)
            logger.info("Database initialized at %s", self.db_path)

    def save_company(self, company: Company) -> int:
        """Save or update a company.
        
        Returns:
            Database ID of the company
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM companies WHERE website = ?", (company.website,))
            existing = cursor.fetchone()

            # Serialize JSON fields
            tech_stack = json.dumps(company.tech_stack or [])
            locations = json.dumps(company.locations or [])
            metadata = json.dumps(company.metadata or {})
            now = datetime.now(UTC).isoformat()

            if existing:
                # Update existing
                company_id = existing[0]
                cursor.execute("""
                    UPDATE companies 
                    SET name=?, careers_url=?, industry=?, size=?, description=?,
                        tech_stack=?, locations=?, funding_stage=?, metadata=?, updated_at=?
                    WHERE id=?
                """, (company.name, company.careers_url, company.industry.value, company.size.value,
                      company.description, tech_stack, locations, company.funding_stage, 
                      metadata, now, company_id))
                logger.debug("Updated company: %s (ID: %d)", company.name, company_id)
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO companies (
                        name, website, careers_url, industry, size, description,
                        tech_stack, locations, funding_stage, discovered_via,
                        discovered_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (company.name, company.website, company.careers_url, company.industry.value,
                      company.size.value, company.description, tech_stack, locations,
                      company.funding_stage, company.discovered_via, 
                      company.discovered_at.isoformat(), metadata))
                company_id = cursor.lastrowid
                assert company_id is not None
                logger.info("Saved new company: %s (ID: %d)", company.name, company_id)

            conn.commit()
            return company_id

    def get_company(self, company_id: int) -> Optional[Company]:
        """Retrieve a company by ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
            row = cursor.fetchone()
            return self._row_to_company(row) if row else None

    def find_companies(
        self,
        industries: Optional[list[IndustryType]] = None,
        sizes: Optional[list[CompanySize]] = None,
        locations: Optional[list[str]] = None,
        tech_stack: Optional[list[str]] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> list[Company]:
        """Find companies matching criteria."""
        query = "SELECT * FROM companies WHERE 1=1"
        params = []

        if active_only:
            query += " AND active = 1"

        if industries:
            placeholders = ",".join("?" * len(industries))
            query += f" AND industry IN ({placeholders})"
            params.extend([ind.value for ind in industries])

        if sizes:
            placeholders = ",".join("?" * len(sizes))
            query += f" AND size IN ({placeholders})"
            params.extend([size.value for size in sizes])

        if locations:
            query += " AND (" + " OR ".join(["locations LIKE ?"] * len(locations)) + ")"
            params.extend([f'%"{loc}"%' for loc in locations])

        if tech_stack:
            query += " AND (" + " OR ".join(["tech_stack LIKE ?"] * len(tech_stack)) + ")"
            params.extend([f'%"{tech}"%' for tech in tech_stack])

        query += " ORDER BY discovered_at DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [self._row_to_company(row) for row in cursor.fetchall()]

    def update_careers_url(self, company_id: int, careers_url: str) -> bool:
        """Update careers URL for a company."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE companies SET careers_url=?, updated_at=? WHERE id=?",
                (careers_url, datetime.now(UTC).isoformat(), company_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def mark_company_checked(self, company_id: int):
        """Update last_checked timestamp."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE companies SET last_checked=? WHERE id=?",
                (datetime.now(UTC).isoformat(), company_id)
            )
            conn.commit()

    def log_discovery(
        self,
        source: str,
        companies_found: int,
        companies_new: int,
        companies_updated: int,
        errors: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
        duration_seconds: Optional[float] = None,
    ):
        """Log a discovery operation."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO discovery_log (
                    source, timestamp, companies_found, companies_new,
                    companies_updated, errors, metadata, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (source, datetime.now(UTC).isoformat(), companies_found, companies_new,
                  companies_updated, json.dumps(errors or []), json.dumps(metadata or {}),
                  duration_seconds))
            conn.commit()
            logger.info("Logged discovery: %s - %d new, %d updated", source, companies_new, companies_updated)

    def get_stats(self) -> dict:
        """Get database statistics."""
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM companies WHERE active = 1")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT industry, COUNT(*) as count
                FROM companies WHERE active = 1
                GROUP BY industry ORDER BY count DESC
            """)
            by_industry = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT size, COUNT(*) as count
                FROM companies WHERE active = 1
                GROUP BY size ORDER BY count DESC
            """)
            by_size = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT source, SUM(companies_new) as total
                FROM discovery_log
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY source
            """)
            discoveries = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_companies": total,
                "by_industry": by_industry,
                "by_size": by_size,
                "discoveries_last_7_days": discoveries,
            }

    def _row_to_company(self, row: sqlite3.Row) -> Company:
        """Convert database row to Company object."""
        return Company(
            name=row["name"],
            website=row["website"],
            careers_url=row["careers_url"],
            industry=IndustryType(row["industry"]),
            size=CompanySize(row["size"]),
            description=row["description"] or "",
            tech_stack=json.loads(row["tech_stack"]) if row["tech_stack"] else [],
            locations=json.loads(row["locations"]) if row["locations"] else [],
            funding_stage=row["funding_stage"],
            discovered_via=row["discovered_via"],
            discovered_at=datetime.fromisoformat(row["discovered_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

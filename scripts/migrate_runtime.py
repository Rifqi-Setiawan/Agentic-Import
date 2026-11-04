"""Additive application migration; run explicitly before starting a new worker."""
import psycopg
from src.core.config import settings

def migrate():
    with psycopg.connect(settings.DATABASE_URL) as db:
        name=db.execute("SELECT current_database()").fetchone()[0]
        if name not in ("imporjaga", "imporjaga_test"):
            raise RuntimeError("Unexpected database; migration refused")
        db.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS run_after timestamptz NOT NULL DEFAULT NOW()")
        db.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT NOW()")
        db.execute("CREATE TABLE IF NOT EXISTS worker_heartbeat(id integer PRIMARY KEY, last_seen timestamptz NOT NULL)")
        db.execute("ALTER TABLE shipments DROP CONSTRAINT IF EXISTS shipments_shipment_number_key")
        db.execute("DROP INDEX IF EXISTS ix_shipments_shipment_number")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_shipments_company_ref ON shipments(company_id,shipment_number)")
        db.execute("CREATE INDEX IF NOT EXISTS ix_jobs_ready ON jobs(run_after,id) WHERE status='queued'")
    return name
if __name__ == "__main__":
    print("Migrated",migrate())

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
        db.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS has_api boolean")
        db.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS autonomy_level varchar(10) NOT NULL DEFAULT 'assist'")
        db.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS incoterm varchar(3)")
        db.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS freight_value numeric(18,2)")
        db.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS insurance_value numeric(18,2)")
        db.execute("ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS approval_origin varchar(32)")
        db.execute("""CREATE TABLE IF NOT EXISTS exchange_rates (
            currency varchar(3) NOT NULL, valid_from date NOT NULL, valid_until date NOT NULL,
            rate numeric(18,4) NOT NULL CHECK (rate > 0), source text NOT NULL,
            PRIMARY KEY (currency, valid_from), CHECK (valid_until >= valid_from)
        )""")
        db.execute("""INSERT INTO jobs (shipment_id,company_id,event_type,dedupe_key,payload,status,created_at)
            SELECT m.shipment_id,m.company_id,'send_email','mail-' || m.dedupe_key,
                   jsonb_build_object('message_id',m.id,'reminder',true),'queued',NOW()
            FROM messages m
            JOIN jobs previous ON previous.dedupe_key=m.dedupe_key
                AND previous.company_id=m.company_id AND previous.shipment_id=m.shipment_id
                AND previous.event_type='followup' AND previous.status='completed'
            WHERE m.delivery_status='pending' AND m.dedupe_key LIKE 'reminder:%%'
                AND EXISTS (SELECT 1 FROM clarifications c WHERE c.shipment_id=m.shipment_id
                    AND c.company_id=m.company_id AND c.status='open')
            ON CONFLICT (dedupe_key) DO NOTHING""")
        db.execute("ALTER TABLE shipments DROP CONSTRAINT IF EXISTS shipments_shipment_number_key")
        db.execute("DROP INDEX IF EXISTS ix_shipments_shipment_number")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_shipments_company_ref ON shipments(company_id,shipment_number)")
        db.execute("CREATE INDEX IF NOT EXISTS ix_jobs_ready ON jobs(run_after,id) WHERE status='queued'")
    return name
if __name__ == "__main__":
    print("Migrated",migrate())

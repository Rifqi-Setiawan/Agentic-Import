"""Bootstrap a dedicated fictional workspace in a local development database."""
import psycopg

from scripts.import_reference_catalog import import_catalog
from scripts.migrate_runtime import migrate
from src.api.admin_routes import seed_data
from src.core.config import settings
from src.core.database import init_db
from src.core.security import get_password_hash


def main():
    if settings.APP_ENV not in ("development", "test"):
        raise SystemExit("Demo bootstrap requires APP_ENV=development or test.")
    init_db()
    migrate()
    with psycopg.connect(settings.DATABASE_URL) as db, db.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email='admin@mitrakemas.example'")
        if cur.fetchone():
            raise SystemExit("Demo accounts already exist. Use the configured workspace reset to reload fixtures.")
        cur.execute("""INSERT INTO companies (name,npwp,is_active,has_api,created_at)
            VALUES ('PT Mitra Kemas Nusantara','01.234.567.8-012.000',true,true,NOW()) RETURNING id""")
        company_id = cur.fetchone()[0]
        password_hash = get_password_hash("imporjaga123")
        for address, name, role in (
            ("staf", "Staf Impor", "importer_staff"),
            ("reviewer", "Reviewer Kepabeanan", "ppjk_reviewer"),
            ("admin", "Admin Logistik", "admin"),
        ):
            cur.execute("""INSERT INTO users (company_id,email,full_name,password_hash,role,is_active,created_at)
                VALUES (%s,%s,%s,%s,%s,true,NOW())""",
                (company_id, f"{address}@mitrakemas.example", name, password_hash, role))
        import_catalog(db)
        seed_data(cur, company_id)
    print(f"Workspace demo dibuat. Set DEMO_COMPANY_ID={company_id} untuk mengaktifkan reset.")


if __name__ == "__main__":
    main()

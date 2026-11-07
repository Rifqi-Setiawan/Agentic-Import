"""Single-worker durable dispatcher. All effects are persisted before acknowledgement."""
import logging
import threading
import time
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.agent.graph import build_analysis_graph
from src.core.config import settings
from src.worker.outbox import process_outbox_message

LOGGER = logging.getLogger(__name__)


def reclaim_stale_job_leases(db=None):
    if db is not None:
        from src.models.entities import Job
        now = datetime.now(UTC)
        jobs = db.query(Job).filter(Job.status == "processing", Job.lease_expires_at < now).all()
        for job in jobs:
            job.status = "queued"
        db.commit()
        return len(jobs)
    with psycopg.connect(settings.DATABASE_URL) as connection:
        rows = connection.execute("""UPDATE jobs SET status='queued'
            WHERE status='processing' AND lease_expires_at < NOW() RETURNING id""").fetchall()
        return len(rows)


def heartbeat(job_id=None):
    with psycopg.connect(settings.DATABASE_URL) as connection:
        connection.execute("""INSERT INTO worker_heartbeat(id,last_seen) VALUES(1,NOW())
            ON CONFLICT(id) DO UPDATE SET last_seen=NOW()""")
        if job_id:
            connection.execute("UPDATE jobs SET heartbeat_at=NOW(),lease_expires_at=NOW()+INTERVAL '5 minutes' WHERE id=%s AND status='processing'", (job_id,))


def maintain_lease(stop, job_id):
    while not stop.wait(15):
        try:
            heartbeat(job_id)
        except psycopg.Error:
            LOGGER.exception("Worker lease heartbeat failed")


def deliver(connection, job):
    payload = job["payload"] or {}
    message = connection.execute("SELECT * FROM messages WHERE id=%s AND company_id=%s AND shipment_id=%s FOR UPDATE", (payload.get("message_id"),job["company_id"],job["shipment_id"])).fetchone()
    if not message or message["delivery_status"] in ("sent","unknown","cancelled","draft"):
        return
    result = process_outbox_message(dict(message))
    connection.execute("UPDATE messages SET delivery_status=%s,sent_at=CASE WHEN %s='sent' THEN NOW() ELSE sent_at END WHERE id=%s", (result.delivery_status.value,result.delivery_status.value,message["id"]))
    if result.delivery_status.value == "sent" and not payload.get("reminder"):
        key = "followup:" + message["dedupe_key"]
        when = datetime.now(UTC) + timedelta(minutes=settings.FOLLOWUP_DELAY_MINUTES)
        connection.execute("""INSERT INTO jobs(shipment_id,company_id,event_type,dedupe_key,payload,status,run_after,created_at)
            VALUES(%s,%s,'followup',%s,%s,'queued',%s,NOW()) ON CONFLICT(dedupe_key) DO NOTHING""",
            (job["shipment_id"],job["company_id"],key,Jsonb({"message_id":message["id"],
                "document_requirements": payload.get("document_requirements") or []}),when))


def followup(connection, job):
    payload = job["payload"] or {}
    pending = connection.execute("SELECT COUNT(*) AS n FROM clarifications WHERE shipment_id=%s AND company_id=%s AND status='open'", (job["shipment_id"],job["company_id"])).fetchone()["n"]
    if not pending and payload.get("document_requirements"):
        pending = connection.execute("""SELECT COUNT(*) AS n FROM checklist_items
            WHERE shipment_id=%s AND company_id=%s AND status='missing' AND requirement_code=ANY(%s)""",
            (job["shipment_id"], job["company_id"], payload["document_requirements"])).fetchone()["n"]
    if not pending:
        return
    message = connection.execute(
        "SELECT * FROM messages WHERE id=%s AND company_id=%s AND shipment_id=%s",
        (payload.get("message_id"), job["company_id"], job["shipment_id"]),
    ).fetchone()
    if message:
        key = "reminder:" + message["dedupe_key"]
        reminder = connection.execute("""INSERT INTO messages(shipment_id,company_id,dedupe_key,recipient,subject,body,delivery_status,created_at)
            VALUES(%s,%s,%s,%s,%s,%s,'pending',NOW()) ON CONFLICT(dedupe_key) DO NOTHING RETURNING id""", (job["shipment_id"],job["company_id"],key,message["recipient"],"Pengingat — "+message["subject"],message["body"])).fetchone()
        if not reminder:
            reminder = connection.execute("""SELECT id FROM messages
                WHERE dedupe_key=%s AND company_id=%s AND shipment_id=%s AND delivery_status='pending'""",
                (key, job["company_id"], job["shipment_id"])).fetchone()
        if reminder:
            connection.execute("""INSERT INTO jobs(shipment_id,company_id,event_type,dedupe_key,payload,status,run_after,created_at)
                VALUES(%s,%s,'send_email',%s,%s,'queued',NOW(),NOW()) ON CONFLICT(dedupe_key) DO NOTHING""", (job["shipment_id"],job["company_id"],"mail-"+key,Jsonb({"message_id":reminder["id"],"reminder":True})))


def run_once():
    heartbeat()
    reclaim_stale_job_leases()
    with psycopg.connect(settings.DATABASE_URL, row_factory=dict_row) as connection:
        job = connection.execute("SELECT * FROM jobs WHERE status='queued' AND run_after<=NOW() ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1").fetchone()
        if not job:
            return False
        connection.execute("UPDATE jobs SET status='processing',heartbeat_at=NOW(),lease_expires_at=NOW()+INTERVAL '5 minutes' WHERE id=%s", (job["id"],))
        connection.commit()
        stop = threading.Event()
        thread = threading.Thread(target=maintain_lease,args=(stop,job["id"]),daemon=True)
        thread.start()
        run_id = None
        try:
            kind = job["event_type"]
            if kind == "send_email":
                deliver(connection,job)
            elif kind == "followup":
                followup(connection,job)
            else:
                shipment = connection.execute("SELECT * FROM shipments WHERE id=%s AND company_id=%s", (job["shipment_id"],job["company_id"])).fetchone()
                if not shipment or shipment["status"] == "arrived":
                    connection.execute("UPDATE jobs SET status='completed' WHERE id=%s", (job["id"],))
                    return True
                payload = job["payload"] or {}
                mode = "recalc_only" if kind in ("recalculate_compliance","review_decision","review_approved","new_rule","recalc") or payload.get("mode") == "recalc_only" else payload.get("mode","auto")
                run_id = connection.execute("""INSERT INTO agent_runs(shipment_id,company_id,mode,input_version,target_item_ids,status,started_at,total_tokens,cost_usd)
                    VALUES(%s,%s,%s,%s,%s,'running',NOW(),0,NULL) RETURNING id""", (job["shipment_id"],job["company_id"],mode,shipment["input_version"],Jsonb(payload.get("target_item_ids")))).fetchone()["id"]
                connection.commit()
                state = {"shipment_id":str(job["shipment_id"]),"company_id":str(job["company_id"]),"run_id":str(run_id),"mode":mode,"event_type":kind,"input_version":shipment["input_version"],"target_item_ids":payload.get("target_item_ids"),"items":[],"documents":[],"steps_log":[]}
                state["regulation_id"] = payload.get("regulation_id")
                result = build_analysis_graph().invoke(state)
                connection.execute("UPDATE agent_runs SET status='succeeded',outcome=%s,ended_at=NOW() WHERE id=%s", (result["outcome"],run_id))
            connection.execute("UPDATE jobs SET status='completed' WHERE id=%s", (job["id"],))
            connection.commit()
        except Exception:
            connection.rollback()
            LOGGER.exception("Job failed id=%s type=%s", job["id"],job["event_type"])
            connection.execute("UPDATE jobs SET status='failed' WHERE id=%s", (job["id"],))
            if run_id:
                connection.execute("UPDATE agent_runs SET status='failed',ended_at=NOW() WHERE id=%s", (run_id,))
            connection.commit()
        finally:
            stop.set()
            thread.join(timeout=2)
    return True


def run_worker_loop():
    logging.basicConfig(level=logging.INFO)
    # One executor per application: prevents simultaneous passes for one shipment.
    with psycopg.connect(settings.DATABASE_URL,autocommit=True) as lock:
        if not lock.execute("SELECT pg_try_advisory_lock(731903481)").fetchone()[0]:
            raise RuntimeError("An ImporJaga worker is already active")
        while True:
            try:
                if not run_once():
                    time.sleep(2)
            except psycopg.Error:
                LOGGER.exception("Worker database unavailable")
                time.sleep(5)


if __name__ == "__main__":
    run_worker_loop()

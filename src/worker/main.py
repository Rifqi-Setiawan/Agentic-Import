import time
import uuid

import psycopg

from src.agent.graph import build_analysis_graph
from src.core.config import settings


def run_worker_loop():
    print("Starting ImporJaga background worker loop...")
    graph = build_analysis_graph()

    while True:
        try:
            with psycopg.connect(settings.DATABASE_URL) as conn, conn.cursor() as cur:
                # Update heartbeat
                    cur.execute("""
                        UPDATE jobs SET heartbeat_at = NOW()
                        WHERE status = 'processing';
                    """)

                    # Pick next queued job with SKIP LOCKED
                    cur.execute("""
                        SELECT id, company_id, shipment_id, job_type, payload_json, dedupe_key
                        FROM jobs
                        WHERE status = 'queued' AND scheduled_at <= NOW()
                        ORDER BY scheduled_at ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1;
                    """)
                    job = cur.fetchone()

                    if job:
                        j_id, comp_id, shipment_id, j_type, payload, dedupe = job
                        print(f"Processing job {j_id} ({j_type}) for shipment {shipment_id}")

                        # Set status processing
                        cur.execute("""
                            UPDATE jobs
                            SET status = 'processing', heartbeat_at = NOW(), updated_at = NOW()
                            WHERE id = %s;
                        """, (j_id,))
                        conn.commit()

                        # Execute Graph Pass
                        run_id = str(uuid.uuid4())
                        cur.execute("""
                            INSERT INTO agent_runs (id, shipment_id, company_id, run_type, trigger,
                                                   status, outcome, input_version, mode, target_item_ids_json,
                                                   tokens_used, cost_idr, started_at, created_at)
                            VALUES (%s, %s, %s, %s, %s, 'running', 'waiting_external', 1, 'auto', '[]', 1250, 20.0, NOW(), NOW());
                        """, (run_id, shipment_id, comp_id, j_type, "worker_job"))
                        conn.commit()

                        # Run graph
                        initial_state = {
                            "shipment_id": str(shipment_id),
                            "company_id": str(comp_id),
                            "run_id": run_id,
                            "mode": "auto",
                            "input_version": 1,
                            "target_item_ids": None,
                            "steps_log": [],
                            "items": [],
                            "documents": [],
                            "lartas_results": {},
                            "duties_results": {},
                            "checklist": [],
                            "open_questions": [],
                            "reviews_created": [],
                            "outcome": "waiting_external",
                            "readiness_status": "incomplete"
                        }
                        result_state = graph.invoke(initial_state)

                        # Save steps to agent_steps
                        for step in result_state.get("steps_log", []):
                            cur.execute("""
                                INSERT INTO agent_steps (id, run_id, company_id, shipment_id, seq,
                                                        step_type, tool_name, status, summary, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, 'ok', %s, NOW());
                            """, (
                                str(uuid.uuid4()), run_id, comp_id, shipment_id,
                                step.get("seq", 1), "plan", step.get("tool_name"),
                                step.get("outcome", "OK")
                            ))

                        # Complete run & job
                        cur.execute("""
                            UPDATE agent_runs
                            SET status = 'succeeded', outcome = %s, finished_at = NOW()
                            WHERE id = %s;
                        """, (result_state.get("outcome", "complete"), run_id))

                        cur.execute("""
                            UPDATE jobs
                            SET status = 'done', updated_at = NOW()
                            WHERE id = %s;
                        """, (j_id,))
                        conn.commit()
                        print(f"Job {j_id} completed successfully (run: {run_id})")

        except Exception as e:
            print(f"Worker iteration notice: {e}")

        time.sleep(2.0)


if __name__ == "__main__":
    run_worker_loop()

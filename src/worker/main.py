import json
import time
import traceback

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
                    SELECT id, company_id, shipment_id, event_type, payload, dedupe_key
                    FROM jobs
                    WHERE status = 'queued'
                    ORDER BY created_at ASC
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
                        SET status = 'processing', heartbeat_at = NOW()
                        WHERE id = %s;
                    """, (j_id,))
                    conn.commit()

                    try:
                        # Parse payload
                        if isinstance(payload, str):
                            try:
                                payload_data = json.loads(payload)
                            except Exception:
                                payload_data = {}
                        elif isinstance(payload, dict):
                            payload_data = payload
                        else:
                            payload_data = {}

                        target_items = payload_data.get("target_item_ids")
                        input_ver = payload_data.get("version", 1)

                        # Execute Graph Pass
                        target_json = json.dumps(target_items) if target_items is not None else None
                        cur.execute("""
                            INSERT INTO agent_runs (shipment_id, company_id, mode, input_version, target_item_ids,
                                                   status, outcome, started_at, cost_usd, total_tokens)
                            VALUES (%s, %s, 'auto', %s, %s, 'running', 'waiting_external', NOW(), 0.0020, 1250)
                            RETURNING id;
                        """, (shipment_id, comp_id, input_ver, target_json))
                        run_id = cur.fetchone()[0]
                        conn.commit()

                        # Run graph
                        initial_state = {
                            "shipment_id": str(shipment_id),
                            "company_id": str(comp_id),
                            "run_id": str(run_id),
                            "mode": "auto",
                            "input_version": input_ver,
                            "target_item_ids": target_items,
                            "steps_log": [],
                            "items": [],
                            "documents": [],
                            "lartas_results": {},
                            "duties_results": {},
                            "checklist": [],
                            "open_questions": [],
                            "reviews_created": [],
                            "outcome": "waiting_external",
                            "readiness_status": "incomplete",
                        }
                        result_state = graph.invoke(initial_state)

                        # Save steps to agent_steps
                        for step in result_state.get("steps_log", []):
                            t_input = step.get("tool_input")
                            t_output = step.get("tool_output")
                            cur.execute("""
                                INSERT INTO agent_steps (run_id, shipment_id, seq, step_name, tool_name,
                                                        tool_input, tool_output, step_outcome, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
                            """, (
                                run_id, shipment_id,
                                step.get("seq", 1),
                                step.get("step_name", "step"),
                                step.get("tool_name"),
                                json.dumps(t_input) if t_input is not None else None,
                                json.dumps(t_output) if t_output is not None else None,
                                step.get("outcome", "OK"),
                            ))

                        # Complete run & job
                        cur.execute("""
                            UPDATE agent_runs
                            SET status = 'succeeded', outcome = %s, ended_at = NOW()
                            WHERE id = %s;
                        """, (result_state.get("outcome", "complete"), run_id))

                        cur.execute("""
                            UPDATE jobs
                            SET status = 'completed'
                            WHERE id = %s;
                        """, (j_id,))
                        conn.commit()
                        print(f"Job {j_id} completed successfully (run: {run_id})")

                    except Exception as job_err:
                        print(f"Error processing job {j_id}: {job_err}")
                        traceback.print_exc()
                        try:
                            cur.execute("UPDATE jobs SET status = 'failed' WHERE id = %s;", (j_id,))
                            if "run_id" in locals():
                                cur.execute("UPDATE agent_runs SET status = 'failed', ended_at = NOW() WHERE id = %s;", (run_id,))
                            conn.commit()
                        except Exception as rb_err:
                            print(f"Failed to record job failure: {rb_err}")

        except Exception as e:
            print(f"Worker iteration notice: {e}")

        time.sleep(2.0)


if __name__ == "__main__":
    run_worker_loop()

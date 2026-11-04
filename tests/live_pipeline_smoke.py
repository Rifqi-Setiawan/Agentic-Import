"""Explicit live 9Router smoke on TEST DB only; not part of offline pytest collection.

Run: .venv/bin/python tests/live_pipeline_smoke.py
Leaves numbered fixtures and real trace/usage in imporjaga_test for inspection.
"""
import json
import tempfile
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from reportlab.pdfgen import canvas

from src.agent.graph import build_analysis_graph
from src.core.config import settings


def main():
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    folder = Path(tempfile.mkdtemp(prefix="imj-live-smoke-"))
    settings.STORAGE_VAULT_PATH = str(folder)
    with psycopg.connect(settings.DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        assert cursor.fetchone()[0] == "imporjaga_test", "Refusing live smoke outside isolated test DB"
        cursor.execute("INSERT INTO companies(name,created_at) VALUES ('Live pipeline smoke',NOW()) RETURNING id")
        company_id = cursor.fetchone()[0]
        connection.commit()
    cases = [
        ["1 | INDUCTIVE PROXIMITY SENSOR M12 24VDC PNP 3 WIRE | Quantity 3 PCS | Unit price 12.00 | Line total 36.00"],
        ["1 | CENTRIFUGAL WATER PUMP 2.2 KW 220V INDUSTRIAL | Quantity 2 PCS | Unit price 75.00 | Line total 150.00",
         "2 | ELECTRIC AC INDUCTION MOTOR THREE PHASE 5.5 KW 380V | Quantity 1 PCS | Unit price 100.00 | Line total 100.00"],
    ]
    evidence = []
    for index, lines in enumerate(cases):
        document = folder / f"fresh-invoice-{index}.pdf"
        pdf = canvas.Canvas(str(document))
        y = 790
        for line in [f"Commercial invoice LIVE-{index}", "Currency USD", *lines]:
            pdf.drawString(35, y, line)
            y -= 25
        pdf.save()
        with psycopg.connect(settings.DATABASE_URL) as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO shipments(company_id,shipment_number,supplier_name,supplier_email,currency,exchange_rate,
                cif_total_idr,total_duty_idr,status,readiness_status,input_version,created_at,updated_at)
                VALUES (%s,%s,'Fictitious QA supplier','no-send@example.invalid','USD',16000,0,0,'draft','incomplete',1,NOW(),NOW()) RETURNING id""",
                (company_id, f"LIVE-{company_id}-{index}"))
            shipment_id = cursor.fetchone()[0]
            cursor.execute("""INSERT INTO documents(shipment_id,company_id,doc_type,file_name,file_path,file_size,status,uploaded_at)
                VALUES (%s,%s,'INVOICE',%s,%s,%s,'provided',NOW())""", (shipment_id, company_id, document.name, str(document), document.stat().st_size))
            cursor.execute("""INSERT INTO agent_runs(shipment_id,company_id,mode,input_version,status,total_tokens,started_at)
                VALUES (%s,%s,'assist',1,'running',0,NOW()) RETURNING id""", (shipment_id, company_id))
            run_id = cursor.fetchone()[0]
            connection.commit()
        result = build_analysis_graph().invoke({"shipment_id": str(shipment_id), "company_id": str(company_id),
            "run_id": str(run_id), "mode": "assist", "input_version": 1, "items": [], "documents": [], "steps_log": []})
        with psycopg.connect(settings.DATABASE_URL, row_factory=dict_row) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE agent_runs SET status='succeeded',ended_at=NOW(),outcome=%s WHERE id=%s", (result["outcome"], run_id))
            cursor.execute("SELECT * FROM shipment_items WHERE shipment_id=%s ORDER BY line_no", (shipment_id,))
            items = cursor.fetchall()
            cursor.execute("SELECT total_tokens,cost_usd FROM agent_runs WHERE id=%s", (run_id,))
            usage = cursor.fetchone()
            cursor.execute("SELECT tool_output FROM agent_steps WHERE run_id=%s AND step_name='classification'", (run_id,))
            classifications = [row["tool_output"] for row in cursor.fetchall()]
            assert len(items) == len(lines), (len(items), len(lines))
            assert len(classifications) == len(lines), "Every complete fixture item must yield a validated catalog decision"
            assert usage["total_tokens"] > 0, "No measured gateway tokens"
            assert usage["cost_usd"] is None, "Unpriced model calls must not receive invented cost"
            assert result["outcome"] == "action_required", "Human review remains mandatory for new decisions"
            assert all(item["hs_code_proposed"] and not item["is_approved"] for item in items)
            assert all(record.get("citations") and record.get("rationale") for record in classifications)
            connection.commit()
            record = {"shipment_id": shipment_id, "run_id": run_id, "item_count": len(items),
                      "codes": [item["hs_code_proposed"] for item in items], "total_tokens": usage["total_tokens"], "outcome": result["outcome"]}
            evidence.append(record)
            print(json.dumps(record), flush=True)
    print(json.dumps({"status": "PASS", "company_id": company_id, "cases": evidence}), flush=True)


if __name__ == "__main__":
    main()

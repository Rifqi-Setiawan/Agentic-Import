"""Company-scoped persistence used by the analysis graph.

Each node owns a short connection and commits before returning, so SSE readers can
observe completed work while the graph continues. No model receives SQL access.
"""
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.core.config import settings


@contextmanager
def repository(company_id: int, shipment_id: int, run_id: int):
    with psycopg.connect(settings.DATABASE_URL, row_factory=dict_row) as connection:
        repo = AnalysisRepository(connection, company_id, shipment_id, run_id)
        yield repo
        connection.commit()


class AnalysisRepository:
    def __init__(self, connection, company_id: int, shipment_id: int, run_id: int):
        self.connection = connection
        self.company_id = int(company_id)
        self.shipment_id = int(shipment_id)
        self.run_id = int(run_id)
        self.scope = (self.shipment_id, self.company_id)

    def rows(self, sql: str, params=()) -> list[dict[str, Any]]:
        return self.connection.execute(sql, params).fetchall()

    def one(self, sql: str, params=()) -> dict[str, Any] | None:
        return self.connection.execute(sql, params).fetchone()

    def execute(self, sql: str, params=()):
        return self.connection.execute(sql, params)

    def shipment(self):
        row = self.one("SELECT * FROM shipments WHERE id=%s AND company_id=%s", self.scope)
        if not row:
            raise ValueError("Kiriman tidak ditemukan pada perusahaan run ini.")
        run = self.one("SELECT id FROM agent_runs WHERE id=%s AND shipment_id=%s AND company_id=%s",
                       (self.run_id, *self.scope))
        if not run:
            raise ValueError("Run tidak terhubung ke kiriman/perusahaan ini.")
        return row

    def items(self):
        return self.rows("SELECT * FROM shipment_items WHERE shipment_id=%s AND company_id=%s ORDER BY line_no,id", self.scope)

    def documents(self):
        return self.rows("SELECT * FROM documents WHERE shipment_id=%s AND company_id=%s ORDER BY id", self.scope)

    def trace(self, name: str, summary: str, output=None, tool: str | None = None):
        # Worker serializes a shipment; run-row lock also protects concurrent seq allocation.
        self.execute("SELECT id FROM agent_runs WHERE id=%s AND company_id=%s FOR UPDATE", (self.run_id, self.company_id))
        seq = self.one("SELECT COALESCE(MAX(seq),0)+1 AS seq FROM agent_steps WHERE run_id=%s", (self.run_id,))["seq"]
        self.execute("""INSERT INTO agent_steps
            (run_id,shipment_id,seq,step_name,tool_name,tool_output,step_outcome,created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())""",
            (self.run_id, self.shipment_id, seq, name, tool, Jsonb(output) if output is not None else None, summary))
        self.connection.commit()

    def record_usage(self, response: dict):
        self.execute("UPDATE agent_runs SET total_tokens=COALESCE(total_tokens,0)+%s WHERE id=%s AND company_id=%s",
                     (int(response.get("total_tokens") or 0), self.run_id, self.company_id))

    def checklist(self, code: str, title: str, status: str, item_id=None, reason="", agency="Dokumen kiriman"):
        existing = self.one("""SELECT id FROM checklist_items WHERE shipment_id=%s AND company_id=%s
            AND item_id IS NOT DISTINCT FROM %s AND requirement_code=%s ORDER BY id LIMIT 1""",
            (*self.scope, item_id, code))
        if existing:
            self.execute("UPDATE checklist_items SET status=%s,resolution_reason=%s WHERE id=%s", (status, reason, existing["id"]))
        else:
            self.execute("""INSERT INTO checklist_items
                (shipment_id,company_id,item_id,requirement_code,title,agency,status,required_before_submission,resolution_reason)
                VALUES (%s,%s,%s,%s,%s,%s,%s,true,%s)""", (*self.scope, item_id, code, title, agency, status, reason))

    def ensure_review(self, item_id: int, reason: str, kind="classification"):
        open_review = self.one("""SELECT id FROM review_tasks WHERE shipment_id=%s AND company_id=%s
            AND item_id=%s AND review_type=%s AND status IN ('open','pending') LIMIT 1""", (*self.scope, item_id, kind))
        if not open_review:
            self.execute("""INSERT INTO review_tasks
                (shipment_id,company_id,item_id,review_type,status,notes,created_at)
                VALUES (%s,%s,%s,%s,'open',%s,NOW())""", (*self.scope, item_id, kind, reason))

    def questions(self, item_id=None, status=None):
        sql = "SELECT * FROM clarifications WHERE shipment_id=%s AND company_id=%s"
        params = list(self.scope)
        if item_id is not None:
            sql += " AND item_id=%s"
            params.append(item_id)
        if status is not None:
            sql += " AND status=%s"
            params.append(status)
        return self.rows(sql + " ORDER BY id", tuple(params))

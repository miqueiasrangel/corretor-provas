"""
Serviço para gerenciamento de gabaritos oficiais de prova.
"""

import json
from ..database.db import get_db_connection


class AnswerKeyService:

    @staticmethod
    def list_all() -> list[dict]:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, num_questions, created_at FROM answer_keys ORDER BY id DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(key_id: int) -> dict | None:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, name, num_questions, answers_json, created_at FROM answer_keys WHERE id = ?",
                (key_id,)
            ).fetchone()
            if not row:
                return None
            res = dict(row)
            res["answers"] = {int(k): v for k, v in json.loads(res["answers_json"]).items()}
            return res

    @staticmethod
    def create(name: str, answers_dict: dict[int, str], num_questions: int = 40) -> int:
        answers_json = json.dumps({str(k): v.upper() for k, v in answers_dict.items()})
        with get_db_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO answer_keys (name, num_questions, answers_json) VALUES (?, ?, ?)",
                (name, num_questions, answers_json)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def delete(key_id: int) -> bool:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM answer_keys WHERE id = ?", (key_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def seed_default_if_empty():
        """Cria um gabarito padrão caso a tabela esteja vazia."""
        with get_db_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM answer_keys").fetchone()[0]
            if count == 0:
                # Gera um gabarito cíclico A, B, C, D, E para as 40 questões
                options = ["A", "B", "C", "D", "E"]
                sample_answers = {q: options[(q - 1) % 5] for q in range(1, 41)}
                AnswerKeyService.create("Gabarito Padrão A3 - Prova Oficial", sample_answers, 40)


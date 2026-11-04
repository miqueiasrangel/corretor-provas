"""
Serviço de Correção e Execução do Pipeline de Visão Computacional.
Orquestra todas as etapas do sistema, desde o pré-processamento até o banco de dados.
"""

import os
import uuid
import cv2
import numpy as np

from ..database.db import get_db_connection
from ..cv.preprocess import to_grayscale, smooth_gaussian
from ..cv.sheet_detector import detect_sheet_corners, calculate_sharpness, order_corners
from ..cv.geometry import rectify_sheet
from ..cv.threshold import binarize_adaptive
from ..cv.grader import grade_sheet_image
from ..cv.layout import SHEET_WIDTH, SHEET_HEIGHT
from .answer_key_service import AnswerKeyService

CAPTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "captures"))
os.makedirs(CAPTURES_DIR, exist_ok=True)


class GradingService:

    @staticmethod
    def process_and_grade(
        image_bgr: np.ndarray,
        answer_key_id: int,
        student_name: str = "Aluno Não Identificado",
        forced_corners: np.ndarray | None = None
    ) -> dict:
        """
        Executa o pipeline completo sobre uma imagem fornecida:
        1. Localização e ordenação dos cantos da folha
        2. Retificação por Homografia (p' = H*p) para 1000x1414
        3. Conversão para cinza e Binarização adaptativa
        4. Leitura das bolhas via Flood Fill / P_k
        5. Comparação com o gabarito oficial e persistência
        """
        answer_key_obj = AnswerKeyService.get_by_id(answer_key_id)
        if not answer_key_obj:
            raise ValueError(f"Gabarito ID {answer_key_id} não encontrado.")

        h, w = image_bgr.shape[:2]

        # 1. Obtenção dos 4 cantos da folha
        corners = forced_corners
        if corners is None:
            corners = detect_sheet_corners(image_bgr)

        # Fallback inteligente: se for um scan direto ou imagem já alinhada
        if corners is None:
            # Se a proporção for próxima de A4 (w/h próximo de 1/1.414 ou h/w próximo de 1.414)
            corners = np.array([
                [0, 0],
                [w - 1, 0],
                [w - 1, h - 1],
                [0, h - 1]
            ], dtype=np.float32)

        # 2. Retificação por Homografia
        rectified_bgr, H = rectify_sheet(image_bgr, corners, SHEET_WIDTH, SHEET_HEIGHT)

        # 3. Pré-processamento e Binarização
        gray = to_grayscale(rectified_bgr)
        blurred = smooth_gaussian(gray)
        binary = binarize_adaptive(blurred)

        # 4. Correção e Feedback Gráfico
        grade_result = grade_sheet_image(
            rectified_sheet=rectified_bgr,
            binary_sheet=binary,
            answer_key=answer_key_obj["answers"],
            use_recursive_floodfill=False
        )

        # 5. Salva a imagem anotada em disco
        filename = f"grade_{uuid.uuid4().hex[:8]}.jpg"
        save_path = os.path.join(CAPTURES_DIR, filename)
        cv2.imwrite(save_path, grade_result["annotated_image"])

        # 6. Salva no banco de dados SQLite
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO gradings (
                    answer_key_id, student_name, correct_count, wrong_count,
                    blank_count, multiple_count, score_percent, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    answer_key_id,
                    student_name,
                    grade_result["correct_count"],
                    grade_result["wrong_count"],
                    grade_result["blank_count"],
                    grade_result["multiple_count"],
                    grade_result["score_percent"],
                    filename
                )
            )
            grading_id = cursor.lastrowid

            # Insere cada questão na tabela answers
            for d in grade_result["details"]:
                conn.execute(
                    """
                    INSERT INTO answers (
                        grading_id, question_num, detected_option,
                        official_option, is_correct, fill_ratio
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        grading_id,
                        d["question"],
                        d["detected"],
                        d["official"],
                        1 if d["is_correct"] else 0,
                        max(d["fills"]) if d["fills"] else 0.0
                    )
                )
            conn.commit()

        grade_result["grading_id"] = grading_id
        grade_result["image_filename"] = filename
        grade_result["student_name"] = student_name
        grade_result["answer_key_name"] = answer_key_obj["name"]
        return grade_result

    @staticmethod
    def get_grading_by_id(grading_id: int) -> dict | None:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT g.*, k.name AS answer_key_name
                FROM gradings g
                JOIN answer_keys k ON g.answer_key_id = k.id
                WHERE g.id = ?
                """,
                (grading_id,)
            ).fetchone()
            if not row:
                return None

            grading_dict = dict(row)
            answers_rows = conn.execute(
                "SELECT * FROM answers WHERE grading_id = ? ORDER BY question_num ASC",
                (grading_id,)
            ).fetchall()
            grading_dict["details"] = [dict(a) for a in answers_rows]
            return grading_dict

    @staticmethod
    def list_recent_gradings(limit: int = 15) -> list[dict]:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT g.id, g.student_name, g.correct_count, g.score_percent,
                       g.created_at, g.image_path, k.name AS answer_key_name
                FROM gradings g
                JOIN answer_keys k ON g.answer_key_id = k.id
                ORDER BY g.id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]


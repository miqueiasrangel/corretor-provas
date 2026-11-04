"""
Etapa 8 do pipeline: Classificação das Respostas, Comparação com Gabarito e Feedback Gráfico.
Implementa o Algoritmo 2 (grade_sheet) da Entrega 2.
Regras de Decisão:
- P_k >= MARK_THRESHOLD (0.45): alternativa considerada preenchida.
- 0 alternativas marcadas: "BLANK" (em branco).
- 1 alternativa marcada: letra correspondente ('A', 'B', 'C', 'D', 'E').
- >1 alternativas marcadas: "MULTIPLE" (dupla marcação / anulada).
"""

import numpy as np
import cv2
from .layout import (
    NUM_QUESTIONS,
    OPTIONS,
    NUM_OPTIONS,
    MARK_THRESHOLD,
    MEASURE_RADIUS,
    BUBBLE_RADIUS,
    get_bubble_center
)
from .bubbles import calculate_fill_ratio_fast, calculate_fill_ratio_recursive


def classify_question_fill(fill_values: list[float], threshold: float = MARK_THRESHOLD) -> tuple[str, list[int]]:
    """
    Classifica a resposta de uma questão baseada nos índices P_k das alternativas.
    Retorna (status_ou_letra, indices_marcados).
    """
    marked_indices = [i for i, val in enumerate(fill_values) if val >= threshold]

    if len(marked_indices) == 1:
        return OPTIONS[marked_indices[0]], marked_indices
    elif len(marked_indices) == 0:
        return "BLANK", []
    else:
        return "MULTIPLE", marked_indices


def grade_sheet_image(
    rectified_sheet: np.ndarray,
    binary_sheet: np.ndarray,
    answer_key: dict[int, str],
    use_recursive_floodfill: bool = False
) -> dict:
    """
    Executa a leitura das 40 questões na folha retificada e binarizada,
    compara com o gabarito oficial cadastrado e produz a anotação visual.

    Retorna dicionário completo com:
      - 'answers': dicionário {num_questao: 'A'|'B'|'C'|'D'|'E'|'BLANK'|'MULTIPLE'}
      - 'fill_ratios': dicionário {num_questao: [P_A, P_B, P_C, P_D, P_E]}
      - 'correct_count': int
      - 'wrong_count': int
      - 'blank_count': int
      - 'multiple_count': int
      - 'score_percent': float
      - 'annotated_image': np.ndarray (BGR com marcações visuais em verde/vermelho)
      - 'details': lista de dicts com o status individual de cada questão
    """
    annotated = rectified_sheet.copy()
    if len(annotated.shape) == 2:
        annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

    answers = {}
    fill_ratios_dict = {}
    details = []

    correct_count = 0
    wrong_count = 0
    blank_count = 0
    multiple_count = 0

    measure_fn = calculate_fill_ratio_recursive if use_recursive_floodfill else calculate_fill_ratio_fast

    for q in range(1, NUM_QUESTIONS + 1):
        q_fills = []
        q_centers = []

        for opt_idx in range(NUM_OPTIONS):
            cx, cy = get_bubble_center(q, opt_idx)
            q_centers.append((cx, cy))
            pk = measure_fn(binary_sheet, cx, cy, MEASURE_RADIUS)
            q_fills.append(round(pk, 4))

        detected_ans, marked_indices = classify_question_fill(q_fills, MARK_THRESHOLD)
        answers[q] = detected_ans
        fill_ratios_dict[q] = q_fills

        official_ans = answer_key.get(q, "").upper()
        is_correct = (detected_ans == official_ans) and (official_ans != "")

        if detected_ans == "BLANK":
            blank_count += 1
            status = "BLANK"
        elif detected_ans == "MULTIPLE":
            multiple_count += 1
            status = "MULTIPLE"
        elif is_correct:
            correct_count += 1
            status = "CORRECT"
        else:
            wrong_count += 1
            status = "WRONG"

        # Desenho das anotações gráficas sobre a folha retificada
        for opt_idx, (cx, cy) in enumerate(q_centers):
            opt_letter = OPTIONS[opt_idx]
            is_marked = opt_idx in marked_indices
            is_official = (opt_letter == official_ans)

            if is_marked:
                if is_correct:
                    # Alternativa correta assinalada: círculo verde espesso
                    cv2.circle(annotated, (cx, cy), BUBBLE_RADIUS + 3, (0, 200, 0), 2)
                    cv2.circle(annotated, (cx, cy), 3, (0, 200, 0), -1)
                else:
                    # Alternativa errada ou múltipla assinalada: círculo vermelho espesso
                    cv2.circle(annotated, (cx, cy), BUBBLE_RADIUS + 3, (0, 0, 230), 2)
                    cv2.drawMarker(annotated, (cx, cy), (0, 0, 230), cv2.MARKER_TILTED_CROSS, 14, 2)
            elif is_official and not is_correct:
                # Indica em amarelo/laranja qual era a resposta correta não assinalada
                cv2.circle(annotated, (cx, cy), BUBBLE_RADIUS + 3, (0, 165, 255), 2)

        # Coloca indicador numérico ao lado da questão
        first_cx, first_cy = q_centers[0]
        color_text = (0, 180, 0) if is_correct else (0, 0, 220)
        symbol = "OK" if is_correct else ("--" if detected_ans == "BLANK" else "X")
        cv2.putText(
            annotated,
            symbol,
            (first_cx - 45, first_cy + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color_text,
            1,
            cv2.LINE_AA
        )

        details.append({
            "question": q,
            "detected": detected_ans,
            "official": official_ans,
            "status": status,
            "is_correct": is_correct,
            "fills": q_fills
        })

    score_percent = round((correct_count / NUM_QUESTIONS) * 100.0, 1)

    return {
        "answers": answers,
        "fill_ratios": fill_ratios_dict,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "blank_count": blank_count,
        "multiple_count": multiple_count,
        "score_percent": score_percent,
        "annotated_image": annotated,
        "details": details
    }


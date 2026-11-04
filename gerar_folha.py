"""
Script Gerador da Folha de Respostas Oficial Padronizada (1000x1414 px).
Gera:
1. Folha em branco para impressão/uso oficial ('folha_padrao_a4.png').
2. Folha de teste preenchida com gabarito simulado ('amostra_teste_preenchida.png').
"""

import os
import cv2
import numpy as np

from src.cv.layout import (
    SHEET_WIDTH,
    SHEET_HEIGHT,
    NUM_QUESTIONS,
    OPTIONS,
    QUESTIONS_PER_BLOCK,
    BLOCK_1_ORIGIN,
    BLOCK_2_ORIGIN,
    DELTA_X,
    DELTA_Y,
    BUBBLE_RADIUS,
    FIDUCIAL_SIZE,
    FIDUCIAL_MARGIN,
    get_bubble_center
)


def draw_blank_sheet() -> np.ndarray:
    """Desenha a folha oficial de respostas exatamente conforme a Figura 3 da Entrega 2."""
    # Fundo branco
    sheet = np.ones((SHEET_HEIGHT, SHEET_WIDTH, 3), dtype=np.uint8) * 255

    # 1. Desenha os 4 marcadores fiduciais pretos nos cantos
    # Canto superior esquerdo
    cv2.rectangle(sheet, (FIDUCIAL_MARGIN, FIDUCIAL_MARGIN),
                  (FIDUCIAL_MARGIN + FIDUCIAL_SIZE, FIDUCIAL_MARGIN + FIDUCIAL_SIZE), (0, 0, 0), -1)
    # Canto superior direito
    cv2.rectangle(sheet, (SHEET_WIDTH - FIDUCIAL_MARGIN - FIDUCIAL_SIZE, FIDUCIAL_MARGIN),
                  (SHEET_WIDTH - FIDUCIAL_MARGIN, FIDUCIAL_MARGIN + FIDUCIAL_SIZE), (0, 0, 0), -1)
    # Canto inferior direito
    cv2.rectangle(sheet, (SHEET_WIDTH - FIDUCIAL_MARGIN - FIDUCIAL_SIZE, SHEET_HEIGHT - FIDUCIAL_MARGIN - FIDUCIAL_SIZE),
                  (SHEET_WIDTH - FIDUCIAL_MARGIN, SHEET_HEIGHT - FIDUCIAL_MARGIN), (0, 0, 0), -1)
    # Canto inferior esquerdo
    cv2.rectangle(sheet, (FIDUCIAL_MARGIN, SHEET_HEIGHT - FIDUCIAL_MARGIN - FIDUCIAL_SIZE),
                  (FIDUCIAL_MARGIN + FIDUCIAL_SIZE, SHEET_HEIGHT - FIDUCIAL_MARGIN), (0, 0, 0), -1)

    # 2. Borda externa suave
    cv2.rectangle(sheet, (25, 25), (SHEET_WIDTH - 25, SHEET_HEIGHT - 25), (60, 60, 60), 2)

    # 3. Cabeçalho
    cv2.putText(sheet, "FOLHA DE RESPOSTAS - AVALIACAO OBJETIVA", (160, 100),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (20, 20, 20), 2, cv2.LINE_AA)
    
    cv2.rectangle(sheet, (120, 130), (SHEET_WIDTH - 120, 210), (180, 180, 180), 1)
    cv2.putText(sheet, "Nome: ________________________________________________", (140, 165),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 1, cv2.LINE_AA)
    cv2.putText(sheet, "Matricula: ________________________   Turma: ___________", (140, 195),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 50, 50), 1, cv2.LINE_AA)

    # 4. Cabeçalhos das alternativas dos blocos
    for b_idx, origin in enumerate([BLOCK_1_ORIGIN, BLOCK_2_ORIGIN]):
        ox, oy = origin
        start_q = 1 if b_idx == 0 else 21
        header_y = oy - 45

        # Letras das colunas A, B, C, D, E
        for opt_idx, letter in enumerate(OPTIONS):
            col_x = ox + opt_idx * DELTA_X
            cv2.putText(sheet, letter, (col_x - 7, header_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA)

        # Linha separadora do cabeçalho
        cv2.line(sheet, (ox - 40, header_y + 15), (ox + 4 * DELTA_X + 25, header_y + 15), (150, 150, 150), 1)

    # 5. Desenho das bolhas e números das questões (1 a 40)
    for q in range(1, NUM_QUESTIONS + 1):
        for opt_idx in range(len(OPTIONS)):
            cx, cy = get_bubble_center(q, opt_idx)

            # Se for a primeira opção da questão, desenha o número da questão à esquerda
            if opt_idx == 0:
                q_text = f"{q:02d}"
                cv2.putText(sheet, q_text, (cx - 50, cy + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 1, cv2.LINE_AA)

            # Círculo da bolha
            cv2.circle(sheet, (cx, cy), BUBBLE_RADIUS, (80, 80, 80), 2, cv2.LINE_AA)

    # Rodapé
    footer_text = "Projeto A3 - Estruturas Matematicas e Computacao Grafica | UNIFACS"
    cv2.putText(sheet, footer_text, (200, SHEET_HEIGHT - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (120, 120, 120), 1, cv2.LINE_AA)

    return sheet


def fill_bubble(sheet: np.ndarray, question_num: int, option_letter: str):
    """Preenche com tinta escura (simulando caneta/lápis) a bolha escolhida."""
    opt_idx = OPTIONS.index(option_letter.upper())
    cx, cy = get_bubble_center(question_num, opt_idx)
    # Preenche o círculo com preto/grafite
    cv2.circle(sheet, (cx, cy), BUBBLE_RADIUS - 1, (25, 25, 25), -1, cv2.LINE_AA)


def generate_sample_sheets():
    """Gera a folha limpa e a folha de teste preenchida com amostras."""
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "samples"))
    os.makedirs(out_dir, exist_ok=True)

    # 1. Folha em branco
    blank = draw_blank_sheet()
    blank_path = os.path.join(out_dir, "folha_padrao_a4.png")
    cv2.imwrite(blank_path, blank)
    print(f"[OK] Folha padrao gerada em: {blank_path}")

    # 2. Folha preenchida de teste (40 questões simuladas)
    # Responde 35 corretas seguindo ciclo A, B, C, D, E e 5 intencionalmente erradas/em branco
    filled = draw_blank_sheet()
    cv2.putText(filled, "Arthur Souza Freire", (220, 165),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 120), 2, cv2.LINE_AA)
    cv2.putText(filled, "12345678", (260, 195),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 120), 2, cv2.LINE_AA)

    for q in range(1, NUM_QUESTIONS + 1):
        correct_opt = OPTIONS[(q - 1) % 5]
        if q == 10:
            # Em branco proposital
            continue
        elif q == 25:
            # Dupla marcação proposital
            fill_bubble(filled, q, "B")
            fill_bubble(filled, q, "D")
        elif q == 30:
            # Erro proposital
            wrong_opt = "E" if correct_opt != "E" else "A"
            fill_bubble(filled, q, wrong_opt)
        else:
            fill_bubble(filled, q, correct_opt)

    sample_path = os.path.join(out_dir, "amostra_teste_preenchida.png")
    cv2.imwrite(sample_path, filled)
    print(f"[OK] Amostra de teste preenchida gerada em: {sample_path}")


if __name__ == "__main__":
    generate_sample_sheets()


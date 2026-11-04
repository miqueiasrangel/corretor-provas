"""
Etapa 6 do pipeline: Binarização Adaptativa.
Fundamento Matemático:
B(i, j) = 1 se I(i, j) < T_local; caso contrário 0.
Convenção adotada: 1 (ou 255) representa pixel escuro (tinta/caneta)
                   0 representa pixel claro (fundo da folha).
O limiar adaptativo calcula a média da vizinhança local (bloco) subtraída de uma constante C:
T_local(i, j) = μ_{vizinhos}(i, j) - C.
Isso torna a segmentação imune a sombras e iluminação não uniforme.
"""

import numpy as np
import cv2


def binarize_adaptive(image_gray: np.ndarray, block_size: int = 51, c_constant: int = 10) -> np.ndarray:
    """
    Binariza a folha em tons de cinza retificada.
    Retorna matriz binária onde:
      1 (ou 255) = marcação escura
      0 = papel claro
    """
    # Garante que block_size seja ímpar e >= 3
    if block_size % 2 == 0:
        block_size += 1

    # THRESH_BINARY_INV mapeia pixels menores que o limiar (escuros) para 255 (1)
    binary = cv2.adaptiveThreshold(
        image_gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        c_constant
    )
    return binary

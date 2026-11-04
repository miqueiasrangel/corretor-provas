"""
Etapa 5 do pipeline: Transformação de Perspectiva (Homografia).
Fundamento Matemático (Álgebra Linear):
- Coordenadas Homogêneas: p = [x, y, 1]ᵀ, p' = H * p = [x', y', w']ᵀ
- Coordenadas Cartesianas finais: x_f = x'/w', y_f = y'/w'
- A matriz de homografia H (3x3) possui 8 graus de liberdade e mapeia
  os 4 cantos da folha distorcida para um retângulo canônico A4 (1000x1414).
"""

import numpy as np
import cv2
from .layout import SHEET_WIDTH, SHEET_HEIGHT, TARGET_CORNERS


def compute_homography_dlt(src_pts: np.ndarray, dst_pts: np.ndarray) -> np.ndarray:
    """
    Demonstração formal por Álgebra Linear:
    Calcula a matriz de homografia H (3x3) usando o algoritmo DLT (Direct Linear Transformation).
    Para cada par de pontos correspondentes (x, y) -> (u, v):
      [-x, -y, -1,  0,  0,  0, u*x, u*y, u] * h = 0
      [ 0,  0,  0, -x, -y, -1, v*x, v*y, v] * h = 0
    Resolve o sistema homogêneo Ah = 0 via decomposição em valores singulares (SVD).
    """
    assert len(src_pts) >= 4 and len(dst_pts) >= 4

    A = []
    for (x, y), (u, v) in zip(src_pts, dst_pts):
        A.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        A.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])

    A = np.array(A, dtype=np.float64)

    # Decomposição SVD: A = U * S * Vh
    # A solução que minimiza ||Ah|| sujeita a ||h||=1 é a última linha de Vh
    _, _, Vh = np.linalg.svd(A)
    H = Vh[-1].reshape((3, 3))

    # Normaliza de modo que H[2, 2] = 1 (se diferente de zero)
    if not np.isclose(H[2, 2], 0.0):
        H = H / H[2, 2]

    return H.astype(np.float32)


def get_perspective_matrix(src_corners: np.ndarray, dst_corners: np.ndarray | None = None) -> np.ndarray:
    """
    Obtém a matriz de homografia H mapeando os 4 cantos da folha para as
    dimensões padronizadas A4 (1000x1414).
    """
    if dst_corners is None:
        dst_corners = np.array(TARGET_CORNERS, dtype=np.float32)
    else:
        dst_corners = dst_corners.astype(np.float32)

    src_corners = src_corners.astype(np.float32)
    return cv2.getPerspectiveTransform(src_corners, dst_corners)


def rectify_sheet(image: np.ndarray, corners: np.ndarray, width: int = SHEET_WIDTH, height: int = SHEET_HEIGHT) -> tuple[np.ndarray, np.ndarray]:
    """
    Retifica a folha a partir dos 4 cantos detectados para o plano canônico W x H.
    Retorna a imagem retificada e a matriz H calculada.
    """
    H = get_perspective_matrix(corners)
    rectified = cv2.warpPerspective(image, H, (width, height), flags=cv2.INTER_LINEAR)
    return rectified, H


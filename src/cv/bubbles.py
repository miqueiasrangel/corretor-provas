"""
Etapa 7 do pipeline: Segmentação, Leitura das Bolhas e Relação de Recorrência.
Fundamento Matemático (Indução e Relações de Recorrência):
- Algoritmo 4 da Entrega 2: Flood Fill recursivo e cálculo do Fill Ratio P_k.
- Recorrência:
    FF(p) = 0 se p ∉ R ou B[p] == 0 ou p já visitado (Caso Base)
    FF(p) = 1 + FF(up) + FF(down) + FF(left) + FF(right) (Passo Indutivo)
- P_k = largest_component / |R|
"""

import sys
import numpy as np
from .layout import MEASURE_RADIUS, MARK_THRESHOLD

# Aumenta limite de recursão para permitir percurso recursivo no disco da bolha (~450 pixels)
sys.setrecursionlimit(10000)


def extract_bubble_roi(binary: np.ndarray, cx: int, cy: int, radius: int = MEASURE_RADIUS) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Recorta a região circular R da bolha centrada em (cx, cy) com raio r.
    Retorna:
      roi: submatriz quadrada envolvente
      mask: máscara circular booleana onde True indica pixel dentro do círculo de raio r
      area_r: total de pixels pertencentes a |R|
    """
    h, w = binary.shape
    y1 = max(0, cy - radius)
    y2 = min(h, cy + radius + 1)
    x1 = max(0, cx - radius)
    x2 = min(w, cx + radius + 1)

    roi = binary[y1:y2, x1:x2]

    # Gera máscara circular relativa ao centro local
    yy, xx = np.ogrid[y1 - cy:y2 - cy, x1 - cx:x2 - cx]
    circle_mask = (xx * xx + yy * yy) <= (radius * radius)

    area_r = int(np.sum(circle_mask))
    return roi, circle_mask, area_r


def flood_fill_recursive(
    y: int,
    x: int,
    binary_roi: np.ndarray,
    circle_mask: np.ndarray,
    visited: np.ndarray
) -> int:
    """
    Implementação formal do Algoritmo 4 (flood_fill) da Entrega 2.
    Caso Base:
      Se pixel fora do círculo R, ou pixel claro (0), ou já visitado -> retorna 0.
    Passo Indutivo / Recursivo:
      Marca pixel atual e retorna:
      1 + FF(up) + FF(down) + FF(left) + FF(right)
    """
    h, w = binary_roi.shape

    # Verificação de limites da matriz
    if x < 0 or x >= w or y < 0 or y >= h:
        return 0

    # Caso Base (Algoritmo 4, linha 1)
    if not circle_mask[y, x] or binary_roi[y, x] == 0 or visited[y, x]:
        return 0

    # Marcar como visitado (Algoritmo 4, linha 2)
    visited[y, x] = True

    # Relação de Recorrência (Algoritmo 4, linhas 3 e 4)
    size = 1
    size += flood_fill_recursive(y - 1, x, binary_roi, circle_mask, visited)  # up
    size += flood_fill_recursive(y + 1, x, binary_roi, circle_mask, visited)  # down
    size += flood_fill_recursive(y, x - 1, binary_roi, circle_mask, visited)  # left
    size += flood_fill_recursive(y, x + 1, binary_roi, circle_mask, visited)  # right

    return size


def calculate_fill_ratio_recursive(
    binary: np.ndarray,
    cx: int,
    cy: int,
    radius: int = MEASURE_RADIUS
) -> float:
    """
    Calcula a proporção P_k da maior mancha escura conexa dentro da bolha
    utilizando a formulação indutiva por Flood Fill da Entrega 2.
    """
    roi, circle_mask, area_r = extract_bubble_roi(binary, cx, cy, radius)
    if area_r == 0:
        return 0.0

    visited = np.zeros_like(roi, dtype=bool)
    largest = 0

    h, w = roi.shape
    for y in range(h):
        for x in range(w):
            # Se for pixel da bolha (circle_mask), escuro (roi > 0) e não visitado
            if circle_mask[y, x] and roi[y, x] > 0 and not visited[y, x]:
                spot_size = flood_fill_recursive(y, x, roi, circle_mask, visited)
                if spot_size > largest:
                    largest = spot_size

    # P_k = largest / |R|
    p_k = float(largest) / float(area_r)
    return p_k


def calculate_fill_ratio_fast(
    binary: np.ndarray,
    cx: int,
    cy: int,
    radius: int = MEASURE_RADIUS
) -> float:
    """
    Versão equivalente otimizada para processamento rápido de frames em tempo real:
    mede a proporção total de pixels escuros dentro da região R da bolha.
    Para validação teórica formal da rubrica, utilize calculate_fill_ratio_recursive.
    """
    roi, circle_mask, area_r = extract_bubble_roi(binary, cx, cy, radius)
    if area_r == 0:
        return 0.0

    dark_pixels = np.count_nonzero((roi > 0) & circle_mask)
    return float(dark_pixels) / float(area_r)


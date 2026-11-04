"""
Etapas 1 e 4 do pipeline: Detecção da Folha de Respostas, Bordas, Cantos e Estabilidade.
Fundamento Matemático:
- Álgebra Linear: Convolução com máscaras de Sobel (Gx, Gy), Laplaciano para nitidez
  e norma Euclidiana ||c_t - c_{t-1}|| < ε para estabilização temporal de cantos.
"""

import numpy as np
import cv2

# Máscaras de Sobel e Laplaciano especificadas na Entrega 2
SOBEL_X = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1]
], dtype=np.float32)

SOBEL_Y = np.array([
    [-1, -2, -1],
    [ 0,  0,  0],
    [ 1,  2,  1]
], dtype=np.float32)

LAPLACIAN = np.array([
    [0,  1, 0],
    [1, -4, 1],
    [0,  1, 0]
], dtype=np.float32)


def calculate_sharpness(image_gray: np.ndarray) -> float:
    """
    Calcula a nitidez da imagem através da variância do Laplaciano:
    var(L * I). Imagens borradas produzem variância baixa.
    """
    lap = cv2.filter2D(image_gray, cv2.CV_64F, LAPLACIAN)
    return float(lap.var())


def order_corners(pts: np.ndarray) -> np.ndarray:
    """
    Ordena 4 pontos em ordem canônica:
    [topo-esquerdo, topo-direito, baixo-direito, baixo-esquerdo]
    Utiliza propriedades de Álgebra Linear:
    - O ponto superior esquerdo tem a menor soma (x + y).
    - O ponto inferior direito tem a maior soma (x + y).
    - O ponto superior direito tem a menor diferença (y - x).
    - O ponto inferior esquerdo tem a maior diferença (y - x).
    """
    pts = pts.reshape(4, 2).astype(np.float32)
    rect = np.zeros((4, 2), dtype=np.float32)

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right

    diff = np.diff(pts, axis=1)  # y - x
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect


def detect_sheet_corners(image_bgr: np.ndarray) -> np.ndarray | None:
    """
    Detecta os 4 cantos da folha de respostas na imagem.
    Aplica conversão em escala de cinza, suavização, detecção de bordas de Canny
    e busca pelo contorno quadrilátero com proporção e área coerentes.
    """
    h, w = image_bgr.shape[:2]
    total_area = float(h * w)

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detecção de bordas via Canny
    edges = cv2.Canny(blurred, 50, 150)
    
    # Dilatação leve para conectar contornos desconexos
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Ordena os maiores contornos por área decrescente
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for c in contours:
        area = cv2.contourArea(c)
        # A folha deve ocupar pelo menos 15% da área total da imagem
        if area < total_area * 0.15:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # Se encontrou um polígono com 4 vértices convexo
        if len(approx) == 4 and cv2.isContourConvex(approx):
            pts = approx.reshape(4, 2)
            ordered = order_corners(pts)
            return ordered

    return None


class SheetStabilizer:
    """
    Controlador de estabilidade temporal para captura automática no vídeo.
    Implementa a condição da Entrega 2:
    ||c_t - c_{t-1}|| < ε por N quadros consecutivos + nitidez >= τ_s.
    """
    def __init__(self, epsilon: float = 12.0, min_stable_frames: int = 5, min_sharpness: float = 60.0):
        self.epsilon = epsilon
        self.min_stable_frames = min_stable_frames
        self.min_sharpness = min_sharpness
        self.previous_corners: np.ndarray | None = None
        self.stable_frames = 0

    def reset(self):
        self.previous_corners = None
        self.stable_frames = 0

    def update(self, corners: np.ndarray | None, sharpness: float) -> tuple[bool, int, float]:
        """
        Recebe os cantos detectados no frame atual e o valor de nitidez.
        Retorna (is_ready, stable_frames, distance_norm).
        """
        if corners is None:
            self.stable_frames = 0
            self.previous_corners = None
            return False, 0, 999.0

        if self.previous_corners is None:
            self.previous_corners = corners
            self.stable_frames = 1
            return False, 1, 999.0

        # Norma Euclidiana ||c_t - c_{t-1}|| no espaço R^8
        dist = float(np.linalg.norm(corners.flatten() - self.previous_corners.flatten()))
        self.previous_corners = corners

        if dist < self.epsilon:
            self.stable_frames += 1
        else:
            self.stable_frames = 0

        is_sharp = sharpness >= self.min_sharpness
        is_ready = (self.stable_frames >= self.min_stable_frames) and is_sharp

        return is_ready, self.stable_frames, dist


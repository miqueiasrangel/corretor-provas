"""
Etapas 2 e 3 do pipeline: Conversão para tons de cinza e Suavização Gaussiana.
Fundamento Matemático:
- Álgebra Linear: representação matricial da imagem e convolução espacial 2D.
- Conversão Luminância: Y = 0.299*R + 0.587*G + 0.114*B
- Máscara Gaussiana 3x3:
    K_gauss = 1/16 * [[1, 2, 1],
                      [2, 4, 2],
                      [1, 2, 1]]
"""

import numpy as np
import cv2

# Kernel Gaussiano 3x3 conforme definido na Tabela 2 e Algoritmo 3 da Entrega 2
K_GAUSS = np.array([
    [1, 2, 1],
    [2, 4, 2],
    [1, 2, 1]
], dtype=np.float32) / 16.0


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Converte imagem BGR para escala de cinza usando os coeficientes fotométricos:
    Y = 0.299*R + 0.587*G + 0.114*B
    """
    if len(image.shape) == 2:
        return image.copy()
    
    # Se imagem estiver em BGR (padrão OpenCV):
    # Canal 0: Blue, Canal 1: Green, Canal 2: Red
    b = image[:, :, 0].astype(np.float32)
    g = image[:, :, 1].astype(np.float32)
    r = image[:, :, 2].astype(np.float32)

    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return np.clip(gray, 0, 255).astype(np.uint8)


def convolve_manual(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Implementação direta do Algoritmo 3 (convolve) da Entrega 2:
    J(i, j) = Σu Σv K(u, v) * I(i - u, j - v)
    Utilizado para validação acadêmica e testes de rigor matemático.
    """
    m, n = image.shape
    k_h, k_w = kernel.shape
    pad_h, pad_w = k_h // 2, k_w // 2

    # Preenchimento das bordas com reflexão
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect').astype(np.float32)
    output = np.zeros((m, n), dtype=np.float32)

    for i in range(m):
        for j in range(n):
            region = padded[i:i + k_h, j:j + k_w]
            output[i, j] = np.sum(region * kernel)

    return np.clip(output, 0, 255).astype(np.uint8)


def smooth_gaussian(image_gray: np.ndarray, manual: bool = False) -> np.ndarray:
    """
    Aplica suavização com a máscara Gaussiana 3x3 K_GAUSS.
    Se manual=True, executa o loop manual do Algoritmo 3;
    Se manual=False, usa a operação de convolução vetorial otimizada para tempo real.
    """
    if manual:
        return convolve_manual(image_gray, K_GAUSS)
    
    # Convolução vetorial com o mesmo kernel 3x3 da modelagem matemática
    return cv2.filter2D(image_gray, -1, K_GAUSS)


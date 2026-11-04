"""
Bateria de Testes Unitários e Validação dos Fundamentos Matemáticos:
1. Álgebra Linear:
   - Convolução Espacial com máscara Gaussiana 3x3 K_gauss
   - Homografia Projetiva e coordenadas homogêneas p' = H*p
2. Indução e Relações de Recorrência:
   - Caso base e passo indutivo do Flood Fill recursivo (Algoritmo 4)
3. Pipeline Completo:
   - Teste de homologação com folha simulada (37 acertos, 1 erro, 1 branco, 1 múltipla)
"""

import os
import unittest
import numpy as np
import cv2

from src.cv.preprocess import K_GAUSS, convolve_manual, smooth_gaussian, to_grayscale
from src.cv.geometry import compute_homography_dlt, rectify_sheet
from src.cv.bubbles import flood_fill_recursive, calculate_fill_ratio_recursive
from src.cv.threshold import binarize_adaptive
from src.cv.grader import grade_sheet_image
from src.cv.layout import NUM_QUESTIONS, OPTIONS


class TestMathematicalFoundations(unittest.TestCase):

    def test_gaussian_convolution_properties(self):
        """Verifica a normalização do kernel Gaussiano K_gauss (soma dos pesos = 1.0)."""
        kernel_sum = float(np.sum(K_GAUSS))
        self.assertAlmostEqual(kernel_sum, 1.0, places=5,
                               msg="A soma dos pesos do filtro Gaussiano deve ser 1.0 para preservar o brilho médio.")

        # Cria uma imagem sintética 10x10 com um ponto brilhante no centro (impulso unitário)
        impulse = np.zeros((15, 15), dtype=np.uint8)
        impulse[7, 7] = 160

        conv_manual = convolve_manual(impulse, K_GAUSS)
        conv_filter = smooth_gaussian(impulse, manual=False)

        # O centro do impulso suavizado deve ter peso 4/16 = 0.25 -> 160 * 0.25 = 40
        self.assertAlmostEqual(conv_manual[7, 7], 40, delta=2)
        # O resultado manual deve ser numericamente equivalente à versão otimizada
        diff = np.max(np.abs(conv_manual.astype(int) - conv_filter.astype(int)))
        self.assertLessEqual(diff, 2, "Convolução manual e vetorial devem convergir.")

    def test_homography_dlt_svd(self):
        """Verifica a estimação da matriz de homografia H via DLT (SVD) em coordenadas homogêneas."""
        # 4 pontos originais (um retângulo com perspectiva)
        src = np.array([
            [120.0, 80.0],
            [880.0, 110.0],
            [920.0, 950.0],
            [80.0, 900.0]
        ], dtype=np.float32)

        # Destino canônico (retângulo alinhado)
        dst = np.array([
            [0.0, 0.0],
            [1000.0, 0.0],
            [1000.0, 1414.0],
            [0.0, 1414.0]
        ], dtype=np.float32)

        H = compute_homography_dlt(src, dst)
        self.assertEqual(H.shape, (3, 3))

        # Testa a transformação p' = H * p para cada vértice
        for p_src, p_dst in zip(src, dst):
            p_homo = np.array([p_src[0], p_src[1], 1.0], dtype=np.float64)
            p_prime = H @ p_homo
            # Conversão para coordenadas cartesianas: x_f = x'/w', y_f = y'/w'
            w_prime = p_prime[2]
            self.assertNotEqual(w_prime, 0.0)
            x_f = p_prime[0] / w_prime
            y_f = p_prime[1] / w_prime

            self.assertAlmostEqual(x_f, p_dst[0], delta=1.5)
            self.assertAlmostEqual(y_f, p_dst[1], delta=1.5)

    def test_flood_fill_recurrence_induction(self):
        """
        Demonstração do Algoritmo 4:
        Caso Base: mancha vazia (todos pixels 0) -> retorna 0
        Passo Indutivo: mancha conexa de tamanho K -> retorna exatamente K
        """
        roi = np.zeros((15, 15), dtype=np.uint8)
        mask = np.ones((15, 15), dtype=bool)
        visited = np.zeros((15, 15), dtype=bool)

        # Caso Base: pixel não marcado (valor 0)
        base_result = flood_fill_recursive(7, 7, roi, mask, visited)
        self.assertEqual(base_result, 0, "Caso Base deve retornar 0 para pixel não escuro.")

        # Passo Indutivo: cria mancha conexa de 9 pixels (quadrado 3x3)
        roi[6:9, 6:9] = 255
        visited = np.zeros((15, 15), dtype=bool)

        # Chama a recorrência a partir de um pixel pertencente à mancha
        spot_size = flood_fill_recursive(7, 7, roi, mask, visited)
        self.assertEqual(spot_size, 9, "O Flood Fill recursivo deve retornar exatamente a soma indutiva dos 9 pixels conexos.")

    def test_full_pipeline_sample_grading(self):
        """Executa a homologação sobre a folha de teste oficial gerada."""
        sample_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "static", "samples", "amostra_teste_preenchida.png"
        ))
        self.assertTrue(os.path.exists(sample_path), "Arquivo de amostra deve existir.")

        img = cv2.imread(sample_path)
        self.assertIsNotNone(img)

        # Gabarito oficial: padrão cíclico A, B, C, D, E para as 40 questões
        answer_key = {q: OPTIONS[(q - 1) % 5] for q in range(1, NUM_QUESTIONS + 1)}

        gray = to_grayscale(img)
        binary = binarize_adaptive(gray)

        # Correção com o Algoritmo 2
        result = grade_sheet_image(img, binary, answer_key, use_recursive_floodfill=False)

        # Na folha gerada intencionalmente:
        # Q10 = em branco (BLANK)
        # Q25 = dupla marcação (MULTIPLE)
        # Q30 = errada proposital
        # 37 questões corretas
        self.assertEqual(result["answers"][10], "BLANK")
        self.assertEqual(result["answers"][25], "MULTIPLE")
        self.assertEqual(result["blank_count"], 1)
        self.assertEqual(result["multiple_count"], 1)
        self.assertEqual(result["correct_count"], 37)
        self.assertEqual(result["wrong_count"], 1)
        self.assertAlmostEqual(result["score_percent"], 92.5, places=1)


if __name__ == "__main__":
    unittest.main()


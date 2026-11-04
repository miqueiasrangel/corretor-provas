"""
Definições geométricas e constantes do layout da folha de respostas padronizada.
Baseado nas especificações da Entrega 2 (Tabela 3).
"""

# Dimensões da folha retificada no plano homogêneo (proporção A4)
SHEET_WIDTH = 1000
SHEET_HEIGHT = 1414

# Quantidade de questões e alternativas
NUM_QUESTIONS = 40
OPTIONS = ["A", "B", "C", "D", "E"]
NUM_OPTIONS = len(OPTIONS)

# Divisão das questões em 2 blocos (20 questões cada)
QUESTIONS_PER_BLOCK = 20

# Origem de cada bloco: centro da bolha 'A' da primeira questão do bloco
BLOCK_1_ORIGIN = (220, 300)  # Questões 01 a 20
BLOCK_2_ORIGIN = (620, 300)  # Questões 21 a 40

# Espaçamento entre alternativas (horizontal) e entre questões (vertical)
DELTA_X = 60  # px entre centros das bolhas A-B-C-D-E
DELTA_Y = 52  # px entre linhas de questões sucessivas

# Raios da bolha
BUBBLE_RADIUS = 17          # Raio impresso
MEASURE_RADIUS = int(0.7 * BUBBLE_RADIUS)  # Raio interno para amostragem (~12 px)

# Limiar de decisão para marcação (proporção mínima de pixels escuros Pk)
MARK_THRESHOLD = 0.45

# Margens dos 4 marcadores fiduciais nos cantos da folha retificada
# Tamanho do quadrado marcador fiducial: 60x60 px
FIDUCIAL_SIZE = 60
FIDUCIAL_MARGIN = 40

# Cantos teóricos no plano retificado 1000x1414
TARGET_CORNERS = [
    [0.0, 0.0],
    [float(SHEET_WIDTH - 1), 0.0],
    [float(SHEET_WIDTH - 1), float(SHEET_HEIGHT - 1)],
    [0.0, float(SHEET_HEIGHT - 1)]
]


def get_bubble_center(question_num: int, option_idx: int) -> tuple[int, int]:
    """
    Calcula o centro (x, y) no plano retificado da bolha correspondente
    à questão (1 a 40) e à alternativa (0 a 4 para A a E).
    Utiliza a transformação descrita na Entrega 2:
    [x, y, 1]ᵀ = T(x0, y0) * S(Δx, Δy) * [k, q, 1]ᵀ
    """
    if 1 <= question_num <= QUESTIONS_PER_BLOCK:
        x0, y0 = BLOCK_1_ORIGIN
        q_idx = question_num - 1
    elif QUESTIONS_PER_BLOCK < question_num <= NUM_QUESTIONS:
        x0, y0 = BLOCK_2_ORIGIN
        q_idx = question_num - QUESTIONS_PER_BLOCK - 1
    else:
        raise ValueError(f"Questão inválida: {question_num}")

    x = int(round(x0 + option_idx * DELTA_X))
    y = int(round(y0 + q_idx * DELTA_Y))
    return x, y


# Corretor Automático de Provas Objetivas por Visão Computacional

**UNIFACS — Universidade Salvador**  
**Projeto A3 — Estruturas Matemáticas e Computação Gráfica (2026.2)**  
**Professores:** Alberlan Lopes, Inácio Borges, Norberto Maciel  
**Equipe:**
* Arthur Souza Freire
* Miqueias Rangel
* Ruan Cláudio

---

## 1. Visão Geral do Projeto

Este projeto consiste em uma aplicação prática funcional de visão computacional voltada à automatização do processo de correção de avaliações objetivas. O sistema é capaz de capturar imagens de folhas de resposta (seja por fluxo de vídeo ao vivo via câmera de celular/computador ou por upload de fotos), detectar os limites do documento, corrigir distorções de perspectiva através de **Homografia**, binarizar a imagem com limiares adaptativos, segmentar as bolhas de marcação utilizando **Flood Fill Recursivo** e cruzar as respostas detectadas com gabaritos oficiais cadastrados em banco de dados SQLite.

O projeto foi concebido e estruturado em estrita conformidade com as diretrizes do Projeto A3 e com os documentos técnicos elaborados nas etapas anteriores:
* **Entrega 1:** Modelagem teórica da situação-problema e formulação matemática da transformação de perspectiva via matriz homogênea $3 \times 3$.
* **Entrega 2:** Documentação técnica de engenharia, diagrama de camadas da aplicação Flask, modelagem do pipeline em 8 etapas e pseudocódigo formal dos algoritmos centrais.
* **Entrega 3 (Esta Entrega):** Homologação do protótipo funcional executável, repositório de código modularizado e instruções completas de validação experimental.

---

## 2. Fundamentos Matemáticos Integrados

O sistema implementa de forma explícita e determinística os pilares teóricos exigidos na disciplina:

### 2.1 Álgebra Linear

1. **Representação Matricial e Cores:**
   A imagem digital é tratada como uma matriz $I \in \mathbb{R}^{m \times n \times 3}$. A conversão para tons de cinza é realizada através da combinação linear ponderada dos canais RGB:
   $$Y = 0{,}299 R + 0{,}587 G + 0{,}114 B$$

2. **Filtros Espaciais e Convolução 2D ($K_{gauss}$ e Sobel):**
   A suavização da imagem para eliminação de ruídos de alta frequência antes da extração de bordas utiliza a máscara Gaussiana $3 \times 3$ normalizada:
   $$K_{gauss} = \frac{1}{16} \begin{bmatrix} 1 & 2 & 1 \\ 2 & 4 & 2 \\ 1 & 2 & 1 \end{bmatrix}$$
   A convolução discreta $J(i, j) = \sum_u \sum_v K(u, v) \cdot I(i - u, j - v)$ foi formalmente codificada e validada. A detecção de contornos emprega os operadores de Sobel ($G_x, G_y$), e a nitidez temporal é avaliada pela variância do Laplaciano.

3. **Transformação de Perspectiva por Homografia ($p' = H p$):**
   A captura fotográfica oblíqua é retificada mapeando pontos do espaço original $(x, y)$ para o espaço projetivo homogêneo $p = [x, y, 1]^T$. A transformação para o plano canônico $p' = [x', y', w']^T$ é governada pela matriz $H \in \mathbb{R}^{3 \times 3}$:
   $$\begin{bmatrix} x' \\ y' \\ w' \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$
   As coordenadas cartesianas resultantes são obtidas por $x_f = x'/w'$ e $y_f = y'/w'$. Os coeficientes de $H$ são calculados via decomposição em valores singulares (SVD) ou DLT a partir dos 4 cantos da folha, mapeando-os para um retângulo fixo $1000 \times 1414$ px (proporção A4).

4. **Mapeamento Homogêneo da Grade de Respostas:**
   As coordenadas teóricas do centro de cada bolha (questão $q$, alternativa $k$) são descritas no plano retificado por operações de translação e escala:
   $$x = x_0 + k \cdot \Delta x, \quad y = y_0 + q \cdot \Delta y$$

---

### 2.2 Indução Matemática e Relações de Recorrência

Para garantir que marcações manuais sejam diferenciadas de ruídos de impressão ou poeira, o cálculo do preenchimento da bolha utiliza o **Algoritmo de Flood Fill Recursivo** (Algoritmo 4 da Entrega 2):

* **Definição por Recorrência:**
  * **Caso Base:**  
    $$FF(p) = 0 \quad \text{se } p \notin R \lor B[p] = 0 \lor p \in \text{visitados}$$
  * **Passo Recursivo:**  
    $$FF(p) = 1 + FF(\text{cima}) + FF(\text{baixo}) + FF(\text{esquerda}) + FF(\text{direita})$$

* **Demonstração por Indução Matemática:**
  * **Proposição:** Seja $n$ o número de pixels escuros ($B[p]=1$) conexos ainda não visitados na região $R$ da bolha. $FF(p)$ retorna exatamente a cardinalidade da componente conexa que contém $p$.
  * **Caso Base ($n = 0$):** Não há pixels escuros conexos a visitar; a condição do caso base dispara imediatamente devolvendo 0, o que é verdadeiro.
  * **Passo Indutivo:** Assume-se por hipótese indutiva que a chamada recursiva conta com precisão qualquer subconjunto conexo com menos de $n$ pixels. Ao visitar $p$, resta um conjunto de $n - 1$ pixels; cada chamada ortogonal (cima, baixo, esquerda, direita) percorre partes disjuntas da mancha (pois cada pixel visitado é marcado), acumulando $1$ (o próprio pixel $p$) somado à contagem dos vizinhos. Logo, a propriedade é verdadeira para todo $n \in \mathbb{N}$.

O preenchimento final da bolha é dado pela proporção da maior mancha conexa em relação à área total do disco da bolha:
$$P_k = \frac{\max(\text{FloodFill})}{|R|}$$
A alternativa é dada como assinalada se $P_k \ge \tau_m = 0{,}45$.

---

## 3. Arquitetura do Sistema e Estrutura de Pastas

O repositório está organizado em estrita aderência à arquitetura em camadas apresentada na Entrega 2:

```text
corretor-provas/
├── app.py                      # Aplicação web Flask (rotas e ciclo de vida)
├── gerar_folha.py              # Gerador oficial da folha A4 e folhas de teste
├── requirements.txt            # Dependências do projeto (Flask, OpenCV, NumPy)
├── README.md                   # Documento de homologação e instruções da Entrega 3
├── grader.db                   # Banco de dados SQLite persistente
├── src/
│   ├── cv/                     # Módulo de Visão Computacional e Matemática
│   │   ├── __init__.py
│   │   ├── layout.py           # Dimensões (1000x1414), raios e coordenadas da folha
│   │   ├── preprocess.py       # Conversão em tons de cinza e convolução Gaussiana
│   │   ├── sheet_detector.py   # Operadores Sobel, Canny, Laplaciano e estabilidade temporal
│   │   ├── geometry.py         # Matriz de homografia homogênea 3x3 e retificação A4
│   │   ├── threshold.py        # Binarização adaptativa local contra sombras
│   │   ├── bubbles.py          # Flood Fill recursivo e cálculo de P_k
│   │   └── grader.py           # Classificação de alternativas e sobreposição gráfica
│   ├── database/               # Camada de Dados
│   │   ├── __init__.py
│   │   ├── db.py               # Conexão e gerenciamento SQLite
│   │   └── schema.sql          # Esquema das tabelas answer_keys, gradings, answers
│   └── services/               # Camada de Negócio
│       ├── __init__.py
│       ├── answer_key_service.py # CRUD de gabaritos oficiais
│       └── grading_service.py    # Orquestração do pipeline de processamento
├── static/
│   ├── css/
│   │   └── style.css           # Estilização moderna e responsiva
│   ├── js/
│   │   └── scanner.js          # Captura com getUserMedia, canvas overlay e streaming
│   ├── captures/               # Armazenamento das folhas corrigidas com feedback
│   └── samples/                # Folha oficial em branco e amostras simuladas de teste
├── templates/                  # Telas HTML (Jinja2)
│   ├── base.html               # Layout mestre e navegação
│   ├── index.html              # Dashboard com métricas e histórico
│   ├── gabaritos.html          # Cadastro e preenchimento de gabaritos
│   ├── corrigir.html           # Tela de correção (Câmera ao Vivo + Upload)
│   └── resultado.html          # Relatório analítico da prova com anotação visual
└── tests/
    └── test_math_pipeline.py   # Bateria de testes unitários dos fundamentos matemáticos
```

---

## 4. Instruções de Instalação e Execução

### 4.1 Pré-requisitos
* **Python:** Versão 3.11 ou superior instalada no sistema.
* **Navegador Web:** Google Chrome, Microsoft Edge, Firefox ou Safari.

### 4.2 Passo a Passo de Instalação

1. **Acessar a pasta do projeto:**
   ```bash
   cd corretor-provas
   ```

2. **(Opcional, mas recomendado) Criar e ativar um ambiente virtual:**
   * No Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * No Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Gerar os arquivos oficiais da folha de respostas e amostras:**
   ```bash
   python gerar_folha.py
   ```
   *Isso criará a folha padrão em branco (`static/samples/folha_padrao_a4.png`) e a folha de teste preenchida (`static/samples/amostra_teste_preenchida.png`).*

---

## 5. Execução dos Testes Automatizados

Para homologar formalmente os cálculos matemáticos integrados, execute a suíte de testes unitários:

```bash
python -m unittest tests/test_math_pipeline.py
```

A suíte valida:
* A normalização e resposta impulsional da convolução Gaussiana ($K_{gauss}$).
* O cálculo da matriz de Homografia homogênea via decomposição SVD e mapeamento $x_f, y_f$.
* A indução e caso base da relação de recorrência do Flood Fill.
* A correção ponta a ponta da folha de respostas com 40 questões (identificando acertos, erros, questões em branco e duplas marcações).

---

## 6. Como Executar a Aplicação Web

Inicie o servidor Flask com o comando:

```bash
python app.py
```

O terminal exibirá a inicialização do servidor:
```text
Iniciando servidor web Corretor Automático A3 na porta 5000...
 * Running on http://127.0.0.1:5000
```

Abra o navegador e acesse:
```
http://localhost:5000
```

---

## 7. Roteiro de Homologação e Demonstração Prática

Para a apresentação aos professores ou avaliação funcional, o sistema disponibiliza três modos de validação:

### Modo 1: Teste Imediato com Amostra Simulada (1 Clique)
1. No menu superior, clique em **"Corrigir Prova"**.
2. Selecione a aba **"Upload de Imagem / Foto"**.
3. Clique no botão azul **"Testar Imediatamente com Amostra Simulada"**.
4. O sistema processará instantaneamente a folha de teste com 40 questões, aplicando homografia, binarização e medição de bolhas.
5. Você será redirecionado para a tela de resultado detalhado exibindo:
   * **92,5% de aproveitamento** (37 acertos, 1 erro, 1 em branco na Q10, 1 dupla marcação na Q25).
   * Imagem retificada com círculos verdes nos acertos, vermelhos nos erros e laranjas nas respostas esperadas.
   * Tabela analítica com a taxa $P_k$ de cada alternativa.

### Modo 2: Upload de Imagem Fotográfica
1. Clique em **"Folha A4 Padrão"** na barra de navegação para baixar o modelo oficial da folha.
2. Imprima a folha ou faça marcações digitais/fotografe-a mesmo inclinada ou com iluminação ambiente.
3. Na tela de correção, na aba **"Upload de Imagem / Foto"**, arraste ou selecione a fotografia.
4. Clique em **"Processar e Corrigir Folha"**.
5. O sistema identificará automaticamente os cantos, retificará a perspectiva para $1000 \times 1414$ px e computará o resultado.

### Modo 3: Câmera ao Vivo com Captura Automática
1. Na tela de correção, mantenha a aba **"Câmera ao Vivo"** selecionada.
2. Clique em **"Ligar Câmera"** (permita o acesso no navegador).
3. Aponte a câmera para a folha de respostas.
4. O script `scanner.js` desenhará um quadrilátero azul sobre os 4 cantos detectados em tempo real.
5. Ao manter a folha estável por alguns instantes (barra de estabilidade verde cheia), a captura é acionada automaticamente, retificando a folha e apresentando o relatório de notas. Se preferir, é possível clicar em **"Capturar e Corrigir Agora"**.

---

## 8. Considerações Finais da Entrega 3

Com a entrega deste protótipo executável:
* A especificação teórica das Entregas 1 e 2 foi convertida em software funcional, estável e testado.
* Os fundamentos de Álgebra Linear e Indução Matemática estão diretamente integrados ao pipeline de processamento.
* O sistema está completamente preparado para a **Entrega 4 (Apresentação Final e Conclusão)**.


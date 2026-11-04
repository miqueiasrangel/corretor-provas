-- Tabela de Gabaritos Oficiais
CREATE TABLE IF NOT EXISTS answer_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    num_questions INTEGER NOT NULL DEFAULT 40,
    answers_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Correções Realizadas
CREATE TABLE IF NOT EXISTS gradings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_key_id INTEGER NOT NULL,
    student_name TEXT DEFAULT 'Aluno Não Identificado',
    correct_count INTEGER NOT NULL DEFAULT 0,
    wrong_count INTEGER NOT NULL DEFAULT 0,
    blank_count INTEGER NOT NULL DEFAULT 0,
    multiple_count INTEGER NOT NULL DEFAULT 0,
    score_percent REAL NOT NULL DEFAULT 0.0,
    image_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (answer_key_id) REFERENCES answer_keys(id) ON DELETE CASCADE
);

-- Tabela de Respostas Detalhadas por Questão
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grading_id INTEGER NOT NULL,
    question_num INTEGER NOT NULL,
    detected_option TEXT,
    official_option TEXT,
    is_correct BOOLEAN NOT NULL DEFAULT 0,
    fill_ratio REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (grading_id) REFERENCES gradings(id) ON DELETE CASCADE
);


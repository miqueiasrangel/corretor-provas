"""
Aplicação Principal Flask - Corretor Automático de Provas Objetivas.
Projeto A3 - Estruturas Matemáticas e Computação Gráfica (UNIFACS 2026.2).
"""

import os
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file

from src.database.db import init_db
from src.services.answer_key_service import AnswerKeyService
from src.services.grading_service import GradingService
from src.cv.sheet_detector import detect_sheet_corners, calculate_sharpness, SheetStabilizer
from src.cv.layout import NUM_QUESTIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a3-computacao-grafica-unifacs-2026'

# Instância global do estabilizador de vídeo
stabilizer = SheetStabilizer(epsilon=15.0, min_stable_frames=5, min_sharpness=50.0)


@app.before_request
def setup_on_startup():
    """Garante que o banco de dados e os gabaritos iniciais estejam prontos."""
    if not hasattr(app, '_db_initialized'):
        init_db()
        AnswerKeyService.seed_default_if_empty()
        app._db_initialized = True


@app.route('/')
def index():
    """Dashboard com métricas, gabaritos e histórico recente."""
    answer_keys = AnswerKeyService.list_all()
    gradings = GradingService.list_recent_gradings(limit=15)
    return render_template('index.html', answer_keys=answer_keys, gradings=gradings)


@app.route('/gabaritos', methods=['GET', 'POST'])
def gabaritos():
    """Listagem e cadastro de novos gabaritos oficiais."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip() or "Gabarito Sem Nome"
        answers_dict = {}
        for q in range(1, NUM_QUESTIONS + 1):
            chosen = request.form.get(f'q_{q}', 'A').upper()
            answers_dict[q] = chosen

        key_id = AnswerKeyService.create(name, answers_dict, NUM_QUESTIONS)
        return redirect(url_for('index'))

    return render_template('gabaritos.html')


@app.route('/gabaritos/<int:key_id>/delete', methods=['POST'])
def delete_gabarito(key_id):
    """Exclui um gabarito existente."""
    AnswerKeyService.delete(key_id)
    return redirect(url_for('index'))


@app.route('/corrigir')
def corrigir():
    """Interface de correção por câmera ao vivo ou upload de imagem."""
    answer_keys = AnswerKeyService.list_all()
    selected_key_id = request.args.get('key_id', type=int)
    if not selected_key_id and answer_keys:
        selected_key_id = answer_keys[0]['id']

    return render_template('corrigir.html', answer_keys=answer_keys, selected_key_id=selected_key_id)


@app.route('/api/quadro', methods=['POST'])
def api_quadro():
    """
    Recebe frames de vídeo da câmera via POST JSON.
    Calcula nitidez e cantos da folha, avalia estabilidade temporal
    e, se estável ou solicitado, processa a correção.
    """
    data = request.get_json() or {}
    frame_b64 = data.get('frame')
    key_id = int(data.get('key_id') or 1)
    student_name = data.get('student_name', 'Aluno via Webcam')
    force_grade = bool(data.get('force_grade', False))

    if not frame_b64:
        return jsonify({"success": False, "error": "Quadro não fornecido."}), 400

    try:
        # Decodifica base64 para matriz de imagem OpenCV
        header, encoded = frame_b64.split(",", 1) if "," in frame_b64 else ("", frame_b64)
        image_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"success": False, "error": "Falha na decodificação do quadro."}), 400

        # Detecção de cantos e cálculo da nitidez
        corners = detect_sheet_corners(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharpness = calculate_sharpness(gray)

        # Avaliação de estabilidade temporal
        is_ready, stable_frames, _ = stabilizer.update(corners, sharpness)

        # Se a folha estiver estável ou o usuário clicou em forçar correção
        if force_grade or is_ready:
            stabilizer.reset()
            result = GradingService.process_and_grade(
                image_bgr=frame,
                answer_key_id=key_id,
                student_name=student_name,
                forced_corners=corners
            )
            redirect_url = url_for('ver_correcao', grading_id=result['grading_id'])
            return jsonify({
                "success": True,
                "graded": True,
                "redirect_url": redirect_url
            })

        return jsonify({
            "success": True,
            "graded": False,
            "corners": corners.tolist() if corners is not None else None,
            "sharpness": sharpness,
            "stable_frames": stable_frames,
            "ready": is_ready
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_imagem():
    """
    Recebe imagem via formulário multipart ou ativa a amostra de teste.
    Executa a retificação por homografia e a correção completa.
    """
    key_id = int(request.form.get('answer_key_id') or 1)
    student_name = request.form.get('student_name') or "Aluno via Upload"
    use_sample = request.form.get('use_sample') == 'true'

    is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest') or (use_sample)

    try:
        if use_sample:
            sample_file = os.path.join(app.root_path, 'static', 'samples', 'amostra_teste_preenchida.png')
            image_bgr = cv2.imread(sample_file)
            if image_bgr is None:
                raise FileNotFoundError("Amostra simulada não encontrada.")
        else:
            if 'sheet_image' not in request.files:
                return "Nenhum arquivo enviado", 400
            file = request.files['sheet_image']
            if file.filename == '':
                return "Arquivo inválido", 400
            
            image_bytes = file.read()
            np_arr = np.frombuffer(image_bytes, np.uint8)
            image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image_bgr is None:
                return "Formato de imagem não suportado.", 400

        result = GradingService.process_and_grade(
            image_bgr=image_bgr,
            answer_key_id=key_id,
            student_name=student_name
        )

        redirect_url = url_for('ver_correcao', grading_id=result['grading_id'])

        if is_ajax:
            return jsonify({"success": True, "redirect_url": redirect_url})
        return redirect(redirect_url)

    except Exception as e:
        if is_ajax:
            return jsonify({"success": False, "error": str(e)}), 500
        return f"Erro ao processar imagem: {e}", 500


@app.route('/correcoes/<int:grading_id>')
def ver_correcao(grading_id):
    """Exibe o relatório detalhado da prova corrigida."""
    grading = GradingService.get_grading_by_id(grading_id)
    if not grading:
        return "Correção não encontrada.", 404
    return render_template('resultado.html', grading=grading)


@app.route('/download-folha')
def download_folha():
    """Permite baixar a imagem da folha padronizada oficial para impressão."""
    folha_path = os.path.join(app.root_path, 'static', 'samples', 'folha_padrao_a4.png')
    if not os.path.exists(folha_path):
        import gerar_folha
        gerar_folha.generate_sample_sheets()
    return send_file(folha_path, as_attachment=True, download_name="folha_respostas_padrao_a4.png")


if __name__ == '__main__':
    init_db()
    AnswerKeyService.seed_default_if_empty()
    print("Iniciando servidor web Corretor Automático A3 na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)


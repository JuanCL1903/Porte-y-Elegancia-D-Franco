# Flask App D'Franco - v2 (Interfaz web + Inventario automático)
# Esta app genera catálogos PDF sin límite de fotos, códigos en secuencia
# y portadas personalizadas con logo y título.

from flask import Flask, request, jsonify, send_file
import os
from PIL import Image
from fpdf import FPDF
import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
LOGO_PATH = 'logo.png'  # Coloca tu logo aquí

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ------------------------------------------
# FUNCIÓN: Generar códigos secuenciales
# ------------------------------------------
def generar_codigos(base_nombre, cantidad):
    codigos = []
    for i in range(1, cantidad+1):
        codigo = f"{base_nombre.upper()}-{str(i).zfill(3)}"
        codigos.append(codigo)
    return codigos

# ------------------------------------------
# FUNCIÓN: Crear PDF catálogo
# ------------------------------------------
def crear_catalogo(titulo, fotos, codigos):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=10)

    # Portada
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, titulo, ln=True, align='C')

    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=60, y=40, w=90)
    pdf.ln(120)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, datetime.datetime.now().strftime("%d/%m/%Y"), ln=True, align='C')

    # GRID 3x3
    cell_w = 63
    cell_h = 85
    img_w = 60
    img_h = 60

    row, col = 0, 0

    for img_path, codigo in zip(fotos, codigos):

        # Nueva página solo cuando volvemos al inicio de 3x3
        if row == 0 and col == 0:
            pdf.add_page()

        x = 10 + col * cell_w
        y = 20 + row * cell_h

        # Insertar imagen respetando proporciones
        try:
            pdf.image(img_path, x=x+1, y=y, w=img_w)
        except:
            pdf.set_font('Arial', '', 8)
            pdf.text(x, y + 5, f"Error: {img_path}")

        # Código centrado
        pdf.set_font('Arial', 'B', 10)
        pdf.text(x + cell_w/2 - (pdf.get_string_width(codigo)/2), y + img_h + 8, codigo)

        # Avanzar columnas y filas
        col += 1
        if col == 3:
            col = 0
            row += 1
            if row == 3:
                row = 0

    nombre_archivo = f"{titulo.replace(' ', '_')}.pdf"
    ruta = os.path.join(OUTPUT_FOLDER, nombre_archivo)
    pdf.output(ruta)

    return ruta

# ------------------------------------------
# INTERFAZ WEB
@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>D'Franco App</title>
        <style>
            body { font-family: Arial; background: #f0f0f0; padding: 30px; }
            .card { background: white; padding: 25px; width: 450px; margin:auto; border-radius: 15px; box-shadow:0 0 20px #0002; }
            input, button { width:100%; padding:10px; margin-top:10px; }
            button { background:black; color:white; cursor:pointer; }
        </style>
    </head>
    <body>
        <div class='card'>
            <h2>Generador de Catálogos D'Franco</h2>
            <form action='/generar' method='POST' enctype='multipart/form-data'>
                <input type='text' name='titulo' placeholder='Título del catálogo' required>
                <input type='text' name='base' placeholder='Código base (DFR, MOÑO, etc.)' required>
                <input type='file' name='fotos' multiple required>
                <button type='submit'>Generar Catálogo</button>
            </form>
            <hr>
            <form action='/inventario' method='POST' enctype='multipart/form-data'>
                <h3>Generar Inventario</h3>
                <input type='text' name='base' placeholder='Código base' required>
                <input type='number' name='stock' placeholder='Stock por pieza' required>
                <input type='file' name='fotos' multiple required>
                <button type='submit'>Generar Inventario Excel</button>
            </form>
        </div>
    </body>
    </html>
    """

# ENDPOINT: Generar catálogo PDF
@app.route('/generar', methods=['POST'])
def generar():
    titulo = request.form.get('titulo')
    base_nombre = request.form.get('base')
    files = request.files.getlist('fotos')

    if not titulo or not base_nombre or len(files) == 0:
        return jsonify({"error": "Faltan datos"}), 400

    rutas = []
    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(path)
        rutas.append(path)

    codigos = generar_codigos(base_nombre, len(files))
    pdf_path = crear_catalogo(titulo, rutas, codigos)

    return send_file(pdf_path, as_attachment=True)

# ENDPOINT: Inventario automático (Excel)
import pandas as pd
@app.route('/inventario', methods=['POST'])
def inventario():
    base = request.form.get('base')
    stock = int(request.form.get('stock'))
    files = request.files.getlist('fotos')

    rutas = []
    nombres = []
    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(path)
        rutas.append(path)
        nombres.append(f.filename)

    codigos = generar_codigos(base, len(files))

    df = pd.DataFrame({
        'Código': codigos,
        'Archivo': nombres,
        'Stock': [stock]*len(files)
    })

    excel_path = os.path.join(OUTPUT_FOLDER, f"Inventario_{base}.xlsx")
    df.to_excel(excel_path, index=False)

    return send_file(excel_path, as_attachment=True)(pdf_path, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'walletflow_pro_2026_secure'

# 1. CONFIGURACIÓN E INICIALIZACIÓN (LISTO)
def init_db():
    conn = sqlite3.connect('gastos.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS gastos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT NOT NULL, 
                       monto REAL NOT NULL, categoria_id INTEGER, fecha TEXT NOT NULL, 
                       FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor REAL)''')
    cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('presupuesto_semanal', 0)")
    
    # Categorías iniciales por defecto
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cats = [('Alimentación',), ('Transporte',), ('Vivienda',), ('Ocio',)]
        cursor.executemany("INSERT INTO categorias (nombre) VALUES (?)", cats)
        
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('gastos.db')
    conn.row_factory = sqlite3.Row
    return conn

init_db()

# 2. RUTA PRINCIPAL (DASHBOARD)
@app.route('/')
def index():
    conn = get_db_connection()
    gastos = conn.execute("SELECT g.*, c.nombre as cat_nombre FROM gastos g JOIN categorias c ON g.categoria_id = c.id ORDER BY g.fecha DESC").fetchall()
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    
    # Cálculo de totales para los cuadros de la imagen
    total = sum(g['monto'] for g in gastos)
    res_pres = conn.execute("SELECT valor FROM configuracion WHERE clave = 'presupuesto_semanal'").fetchone()
    presupuesto = res_pres['valor'] if res_pres else 0
    conn.close()
    
    return render_template('index.html', gastos=gastos, categorias=categorias, total=total, presupuesto=presupuesto)

# ============================================================
# SECCIÓN PARA KAREN: REGISTRO Y CATEGORÍAS
# ============================================================

@app.route('/registrar_gasto', methods=['POST'])
def registrar_gasto():
    # KAREN: Aquí debes capturar los datos del formulario (descripcion, monto, categoria_id, fecha)
    # e insertar el nuevo registro en la tabla 'gastos'.
    pass

@app.route('/categorias', methods=['GET', 'POST'])
def gestionar_categorias():
    # KAREN: Aquí debes programar que si el método es POST, se guarde una nueva categoría.
    # También debe retornar el render_template con la lista de categorías existentes.
    pass

# ============================================================
# SECCIÓN PARA JUAN: ELIMINACIÓN Y REPORTES
# ============================================================

@app.route('/eliminar/<int:id>')
def eliminar_gasto(id):
    # JUAN: Aquí debes programar el DELETE para borrar el registro por ID.
    # No olvides usar el flash() para mostrar el aviso amarillo de "Registro eliminado".
    pass

@app.route('/reportes')
def reportes():
    # JUAN: Aquí debes programar la lógica para filtrar gastos por categoría.
    # Debe sumar el total de la categoría seleccionada y mostrarlo en 'reportes.html'.
    pass

# ============================================================
# CONFIGURACIÓN ADICIONAL (PRESUPUESTO)
# ============================================================

@app.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute("UPDATE configuracion SET valor = ? WHERE clave = 'presupuesto_semanal'", (request.form['presupuesto'],))
        conn.commit()
        flash("Presupuesto actualizado correctamente", "success")
        return redirect(url_for('index'))
    res = conn.execute("SELECT valor FROM configuracion WHERE clave = 'presupuesto_semanal'").fetchone()
    conn.close()
    return render_template('config.html', presupuesto=res['valor'] if res else 0)

if __name__ == '__main__':
    app.run(debug=True)

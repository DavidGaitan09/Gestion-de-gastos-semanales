from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'walletflow_pro_2026_secure'

def init_db():
    conn = sqlite3.connect('gastos.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT NOT NULL, monto REAL NOT NULL, categoria_id INTEGER, fecha TEXT NOT NULL, FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor REAL)''')
    cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('presupuesto_semanal', 0)")
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('gastos.db')
    conn.row_factory = sqlite3.Row
    return conn

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    gastos = conn.execute("SELECT g.*, c.nombre as cat_nombre FROM gastos g JOIN categorias c ON g.categoria_id = c.id ORDER BY g.fecha DESC").fetchall()
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    total = sum(g['monto'] for g in gastos)
    res_pres = conn.execute("SELECT valor FROM configuracion WHERE clave = 'presupuesto_semanal'").fetchone()
    presupuesto = res_pres['valor'] if res_pres else 0
    conn.close()
    
    # ALERTA DE PRESUPUESTO SUPERADO
    if presupuesto > 0 and total > presupuesto:
        flash(f"¡Atención! Has superado tu presupuesto semanal por ${total - presupuesto:,.0f}", "danger")
    
    return render_template('index.html', gastos=gastos, categorias=categorias, total=total, presupuesto=presupuesto)

@app.route('/registrar_gasto', methods=['POST'])
def registrar_gasto():
    conn = get_db_connection()
    conn.execute("INSERT INTO gastos (descripcion, monto, categoria_id, fecha) VALUES (?, ?, ?, ?)",
                 (request.form['descripcion'], request.form['monto'], request.form['categoria_id'], request.form['fecha']))
    conn.commit()
    conn.close()
    flash("Gasto registrado correctamente", "success")
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>')
def eliminar_gasto(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM gastos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Registro eliminado permanentemente", "warning")
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_gasto(id):
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute("UPDATE gastos SET descripcion=?, monto=?, categoria_id=?, fecha=? WHERE id=?",
                     (request.form['descripcion'], request.form['monto'], request.form['categoria_id'], request.form['fecha'], id))
        conn.commit()
        conn.close()
        flash("Registro actualizado con éxito", "success")
        return redirect(url_for('index'))
    gasto = conn.execute("SELECT * FROM gastos WHERE id = ?", (id,)).fetchone()
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    return render_template('editar.html', gasto=gasto, categorias=categorias)

@app.route('/reportes')
def reportes():
    cat_id = request.args.get('categoria_id')
    conn = get_db_connection()
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    query = "SELECT g.*, c.nombre as cat_nombre FROM gastos g JOIN categorias c ON g.categoria_id = c.id"
    if cat_id:
        gastos = conn.execute(query + " WHERE g.categoria_id = ?", (cat_id,)).fetchall()
    else:
        gastos = conn.execute(query).fetchall()
    total_sel = sum(g['monto'] for g in gastos)
    conn.close()
    return render_template('reportes.html', gastos=gastos, categorias=categorias, total_seleccion=total_sel)

@app.route('/historial_mensual')
def historial_mensual():
    mes = request.args.get('mes')
    anio = request.args.get('anio')
    conn = get_db_connection()
    gastos = []
    if mes and anio:
        busqueda = f"{anio}-{mes}%"
        gastos = conn.execute("SELECT g.*, c.nombre as cat_nombre FROM gastos g JOIN categorias c ON g.categoria_id = c.id WHERE g.fecha LIKE ?", (busqueda,)).fetchall()
    total_mes = sum(g['monto'] for g in gastos)
    conn.close()
    return render_template('historial.html', gastos=gastos, total_mes=total_mes)

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

@app.route('/categorias', methods=['GET', 'POST'])
def gestionar_categorias():
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute("INSERT INTO categorias (nombre) VALUES (?)", (request.form['nombre'],))
        conn.commit()
        flash("Nueva categoría añadida", "success")
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    return render_template('categorias.html', categorias=categorias)

if __name__ == '__main__':
    app.run(debug=True)
import sqlite3
import os
from datetime import date


class Database:
    def __init__(self):
        app_dir = os.path.join(
            os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
            'CalasDeAlmeria'
        )
        os.makedirs(app_dir, exist_ok=True)
        self.db_path = os.path.join(app_dir, 'calasdealmeria.db')

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS apartamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                direccion TEXT DEFAULT '',
                planta TEXT DEFAULT '',
                numero TEXT DEFAULT '',
                habitaciones INTEGER DEFAULT 1,
                banos INTEGER DEFAULT 1,
                metros_cuadrados REAL,
                estado TEXT DEFAULT 'libre',
                alquiler_base REAL DEFAULT 0,
                descripcion TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS inquilinos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellidos TEXT DEFAULT '',
                dni_nie TEXT DEFAULT '',
                email TEXT DEFAULT '',
                telefono TEXT DEFAULT '',
                telefono2 TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartamento_id INTEGER NOT NULL,
                inquilino_id INTEGER NOT NULL,
                fecha_inicio DATE NOT NULL,
                fecha_fin DATE,
                alquiler_mensual REAL NOT NULL,
                deposito REAL DEFAULT 0,
                dia_pago INTEGER DEFAULT 1,
                estado TEXT DEFAULT 'activo',
                notas TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apartamento_id) REFERENCES apartamentos(id),
                FOREIGN KEY (inquilino_id) REFERENCES inquilinos(id)
            );

            CREATE TABLE IF NOT EXISTS pagos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contrato_id INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                anyo INTEGER NOT NULL,
                importe REAL NOT NULL,
                fecha_pago DATE,
                fecha_vencimiento DATE,
                tipo TEXT DEFAULT 'alquiler',
                estado TEXT DEFAULT 'pendiente',
                metodo TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contrato_id) REFERENCES contratos(id)
            );

            CREATE TABLE IF NOT EXISTS mantenimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartamento_id INTEGER,
                titulo TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                estado TEXT DEFAULT 'pendiente',
                prioridad TEXT DEFAULT 'media',
                coste REAL DEFAULT 0,
                fecha_reporte DATE DEFAULT CURRENT_DATE,
                fecha_completado DATE,
                proveedor TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apartamento_id) REFERENCES apartamentos(id)
            );

            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartamento_id INTEGER,
                descripcion TEXT NOT NULL,
                importe REAL NOT NULL,
                fecha DATE NOT NULL,
                categoria TEXT DEFAULT 'otro',
                notas TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apartamento_id) REFERENCES apartamentos(id)
            );
        """)
        conn.commit()
        conn.close()

    # ==================== APARTAMENTOS ====================

    def get_apartamentos(self, estado=None):
        conn = self._conn()
        q = "SELECT * FROM apartamentos"
        params = []
        if estado:
            q += " WHERE estado=?"; params.append(estado)
        q += " ORDER BY nombre"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        conn.close()
        return rows

    def get_apartamento(self, id_):
        conn = self._conn()
        row = conn.execute("SELECT * FROM apartamentos WHERE id=?", (id_,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def add_apartamento(self, d):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO apartamentos (nombre,direccion,planta,numero,habitaciones,banos,"
            "metros_cuadrados,estado,alquiler_base,descripcion,notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (d['nombre'], d.get('direccion', ''), d.get('planta', ''), d.get('numero', ''),
             d.get('habitaciones', 1), d.get('banos', 1), d.get('metros_cuadrados') or None,
             d.get('estado', 'libre'), d.get('alquiler_base') or 0,
             d.get('descripcion', ''), d.get('notas', ''))
        )
        conn.commit(); lid = cur.lastrowid; conn.close(); return lid

    def update_apartamento(self, id_, d):
        conn = self._conn()
        conn.execute(
            "UPDATE apartamentos SET nombre=?,direccion=?,planta=?,numero=?,habitaciones=?,banos=?,"
            "metros_cuadrados=?,estado=?,alquiler_base=?,descripcion=?,notas=? WHERE id=?",
            (d['nombre'], d.get('direccion', ''), d.get('planta', ''), d.get('numero', ''),
             d.get('habitaciones', 1), d.get('banos', 1), d.get('metros_cuadrados') or None,
             d.get('estado', 'libre'), d.get('alquiler_base') or 0,
             d.get('descripcion', ''), d.get('notas', ''), id_)
        )
        conn.commit(); conn.close()

    def delete_apartamento(self, id_):
        conn = self._conn()
        conn.execute("DELETE FROM apartamentos WHERE id=?", (id_,))
        conn.commit(); conn.close()

    def get_stats_apartamentos(self):
        conn = self._conn()
        row = conn.execute("""
            SELECT COUNT(*) total,
            SUM(CASE WHEN estado='ocupado' THEN 1 ELSE 0 END) ocupados,
            SUM(CASE WHEN estado='libre' THEN 1 ELSE 0 END) libres,
            SUM(CASE WHEN estado='obras' THEN 1 ELSE 0 END) en_obras,
            SUM(CASE WHEN estado='reservado' THEN 1 ELSE 0 END) reservados
            FROM apartamentos
        """).fetchone()
        conn.close()
        return dict(row) if row else {}

    # ==================== INQUILINOS ====================

    def get_inquilinos(self):
        conn = self._conn()
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM inquilinos ORDER BY apellidos, nombre"
        ).fetchall()]
        conn.close(); return rows

    def get_inquilino(self, id_):
        conn = self._conn()
        row = conn.execute("SELECT * FROM inquilinos WHERE id=?", (id_,)).fetchone()
        conn.close(); return dict(row) if row else None

    def add_inquilino(self, d):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO inquilinos (nombre,apellidos,dni_nie,email,telefono,telefono2,notas) "
            "VALUES (?,?,?,?,?,?,?)",
            (d['nombre'], d.get('apellidos', ''), d.get('dni_nie', ''), d.get('email', ''),
             d.get('telefono', ''), d.get('telefono2', ''), d.get('notas', ''))
        )
        conn.commit(); lid = cur.lastrowid; conn.close(); return lid

    def update_inquilino(self, id_, d):
        conn = self._conn()
        conn.execute(
            "UPDATE inquilinos SET nombre=?,apellidos=?,dni_nie=?,email=?,telefono=?,telefono2=?,notas=? "
            "WHERE id=?",
            (d['nombre'], d.get('apellidos', ''), d.get('dni_nie', ''), d.get('email', ''),
             d.get('telefono', ''), d.get('telefono2', ''), d.get('notas', ''), id_)
        )
        conn.commit(); conn.close()

    def delete_inquilino(self, id_):
        conn = self._conn()
        conn.execute("DELETE FROM inquilinos WHERE id=?", (id_,))
        conn.commit(); conn.close()

    # ==================== CONTRATOS ====================

    def get_contratos(self, estado=None):
        conn = self._conn()
        q = """
            SELECT c.*,
                a.nombre apt_nombre, a.direccion apt_direccion,
                i.nombre || ' ' || COALESCE(i.apellidos,'') inq_nombre,
                i.telefono inq_telefono
            FROM contratos c
            LEFT JOIN apartamentos a ON c.apartamento_id = a.id
            LEFT JOIN inquilinos i ON c.inquilino_id = i.id
        """
        params = []
        if estado:
            q += " WHERE c.estado=?"; params.append(estado)
        q += " ORDER BY c.created_at DESC"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        conn.close(); return rows

    def get_contrato(self, id_):
        conn = self._conn()
        row = conn.execute("""
            SELECT c.*, a.nombre apt_nombre, i.nombre || ' ' || COALESCE(i.apellidos,'') inq_nombre
            FROM contratos c
            LEFT JOIN apartamentos a ON c.apartamento_id = a.id
            LEFT JOIN inquilinos i ON c.inquilino_id = i.id
            WHERE c.id=?
        """, (id_,)).fetchone()
        conn.close(); return dict(row) if row else None

    def add_contrato(self, d):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO contratos (apartamento_id,inquilino_id,fecha_inicio,fecha_fin,"
            "alquiler_mensual,deposito,dia_pago,estado,notas) VALUES (?,?,?,?,?,?,?,?,?)",
            (d['apartamento_id'], d['inquilino_id'], d['fecha_inicio'], d.get('fecha_fin'),
             d['alquiler_mensual'], d.get('deposito', 0) or 0, d.get('dia_pago', 1) or 1,
             d.get('estado', 'activo'), d.get('notas', ''))
        )
        conn.commit()
        if d.get('estado', 'activo') == 'activo':
            conn.execute("UPDATE apartamentos SET estado='ocupado' WHERE id=?", (d['apartamento_id'],))
            conn.commit()
        lid = cur.lastrowid; conn.close(); return lid

    def update_contrato(self, id_, d):
        conn = self._conn()
        conn.execute(
            "UPDATE contratos SET apartamento_id=?,inquilino_id=?,fecha_inicio=?,fecha_fin=?,"
            "alquiler_mensual=?,deposito=?,dia_pago=?,estado=?,notas=? WHERE id=?",
            (d['apartamento_id'], d['inquilino_id'], d['fecha_inicio'], d.get('fecha_fin'),
             d['alquiler_mensual'], d.get('deposito', 0) or 0, d.get('dia_pago', 1) or 1,
             d.get('estado', 'activo'), d.get('notas', ''), id_)
        )
        conn.commit(); conn.close()

    def delete_contrato(self, id_):
        conn = self._conn()
        conn.execute("DELETE FROM contratos WHERE id=?", (id_,))
        conn.commit(); conn.close()

    def get_contratos_activos(self):
        return self.get_contratos(estado='activo')

    # ==================== PAGOS ====================

    def get_pagos(self, contrato_id=None, estado=None, anyo=None, mes=None):
        conn = self._conn()
        q = """
            SELECT p.*,
                a.nombre apt_nombre,
                i.nombre || ' ' || COALESCE(i.apellidos,'') inq_nombre
            FROM pagos p
            LEFT JOIN contratos c ON p.contrato_id = c.id
            LEFT JOIN apartamentos a ON c.apartamento_id = a.id
            LEFT JOIN inquilinos i ON c.inquilino_id = i.id
        """
        conds, params = [], []
        if contrato_id: conds.append("p.contrato_id=?"); params.append(contrato_id)
        if estado: conds.append("p.estado=?"); params.append(estado)
        if anyo: conds.append("p.anyo=?"); params.append(anyo)
        if mes: conds.append("p.mes=?"); params.append(mes)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY p.anyo DESC, p.mes DESC, apt_nombre"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        conn.close(); return rows

    def add_pago(self, d):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO pagos (contrato_id,mes,anyo,importe,fecha_pago,fecha_vencimiento,"
            "tipo,estado,metodo,notas) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (d['contrato_id'], d['mes'], d['anyo'], d['importe'],
             d.get('fecha_pago'), d.get('fecha_vencimiento'),
             d.get('tipo', 'alquiler'), d.get('estado', 'pendiente'),
             d.get('metodo', ''), d.get('notas', ''))
        )
        conn.commit(); lid = cur.lastrowid; conn.close(); return lid

    def update_pago(self, id_, d):
        conn = self._conn()
        conn.execute(
            "UPDATE pagos SET mes=?,anyo=?,importe=?,fecha_pago=?,fecha_vencimiento=?,"
            "tipo=?,estado=?,metodo=?,notas=? WHERE id=?",
            (d['mes'], d['anyo'], d['importe'], d.get('fecha_pago'), d.get('fecha_vencimiento'),
             d.get('tipo', 'alquiler'), d.get('estado', 'pendiente'),
             d.get('metodo', ''), d.get('notas', ''), id_)
        )
        conn.commit(); conn.close()

    def marcar_pagado(self, id_, fecha_pago, metodo=''):
        conn = self._conn()
        conn.execute(
            "UPDATE pagos SET estado='pagado', fecha_pago=?, metodo=? WHERE id=?",
            (fecha_pago, metodo, id_)
        )
        conn.commit(); conn.close()

    def delete_pago(self, id_):
        conn = self._conn()
        conn.execute("DELETE FROM pagos WHERE id=?", (id_,))
        conn.commit(); conn.close()

    def get_resumen_financiero(self, anyo=None):
        yr = anyo or date.today().year
        conn = self._conn()
        p = dict(conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN estado='pagado' THEN importe ELSE 0 END),0) cobrado,
                COALESCE(SUM(CASE WHEN estado IN ('pendiente','retrasado') THEN importe ELSE 0 END),0) pendiente
            FROM pagos WHERE anyo=?
        """, (yr,)).fetchone())
        g = dict(conn.execute(
            "SELECT COALESCE(SUM(importe),0) gastos FROM gastos WHERE strftime('%Y',fecha)=?",
            (str(yr),)
        ).fetchone())
        conn.close()
        cobrado = p['cobrado']
        gastos = g['gastos']
        return {**p, **g, 'neto': cobrado - gastos}

    def get_ingresos_por_mes(self, anyo=None):
        yr = anyo or date.today().year
        conn = self._conn()
        rows = [dict(r) for r in conn.execute("""
            SELECT mes,
                COALESCE(SUM(CASE WHEN estado='pagado' THEN importe ELSE 0 END),0) ingresos,
                COALESCE(SUM(importe),0) esperado
            FROM pagos WHERE anyo=? GROUP BY mes ORDER BY mes
        """, (yr,)).fetchall()]
        conn.close(); return rows

    def get_gastos_por_mes(self, anyo=None):
        yr = anyo or date.today().year
        conn = self._conn()
        rows = [dict(r) for r in conn.execute("""
            SELECT CAST(strftime('%m', fecha) AS INTEGER) mes,
                COALESCE(SUM(importe),0) gastos
            FROM gastos WHERE strftime('%Y',fecha)=? GROUP BY mes ORDER BY mes
        """, (str(yr),)).fetchall()]
        conn.close(); return rows

    # ==================== MANTENIMIENTO ====================

    def get_mantenimiento(self, estado=None, apartamento_id=None):
        conn = self._conn()
        q = """
            SELECT m.*, a.nombre apt_nombre
            FROM mantenimiento m
            LEFT JOIN apartamentos a ON m.apartamento_id = a.id
        """
        conds, params = [], []
        if estado: conds.append("m.estado=?"); params.append(estado)
        if apartamento_id: conds.append("m.apartamento_id=?"); params.append(apartamento_id)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY CASE m.prioridad WHEN 'urgente' THEN 0 WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END, m.created_at DESC"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        conn.close(); return rows

    def add_mantenimiento(self, d):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO mantenimiento (apartamento_id,titulo,descripcion,estado,prioridad,"
            "coste,fecha_reporte,fecha_completado,proveedor,notas) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (d.get('apartamento_id'), d['titulo'], d.get('descripcion', ''),
             d.get('estado', 'pendiente'), d.get('prioridad', 'media'),
             d.get('coste', 0) or 0, d.get('fecha_reporte', str(date.today())),
             d.get('fecha_completado'), d.get('proveedor', ''), d.get('notas', ''))
        )
        conn.commit(); lid = cur.lastrowid; conn.close(); return lid

    def update_mantenimiento(self, id_, d):
        conn = self._conn()
        conn.execute(
            "UPDATE mantenimiento SET apartamento_id=?,titulo=?,descripcion=?,estado=?,prioridad=?,"
            "coste=?,fecha_reporte=?,fecha_completado=?,proveedor=?,notas=? WHERE id=?",
            (d.get('apartamento_id'), d['titulo'], d.get('descripcion', ''),
             d.get('estado', 'pendiente'), d.get('prioridad', 'media'),
             d.get('coste', 0) or 0, d.get('fecha_reporte'),
             d.get('fecha_completado'), d.get('proveedor', ''), d.get('notas', ''), id_)
        )
        conn.commit(); conn.close()

    def delete_mantenimiento(self, id_):
        conn = self._conn()
        conn.execute("DELETE FROM mantenimiento WHERE id=?", (id_,))
        conn.commit(); conn.close()

    def get_stats_mantenimiento(self):
        conn = self._conn()
        row = dict(conn.execute("""
            SELECT
                COUNT(*) total,
                SUM(CASE WHEN estado='pendiente' THEN 1 ELSE 0 END) pendientes,
                SUM(CASE WHEN estado='en_proceso' THEN 1 ELSE 0 END) en_proceso,
                SUM(CASE WHEN estado='completado' THEN 1 ELSE 0 END) completados,
                SUM(CASE WHEN prioridad IN ('alta','urgente') AND estado!='completado' THEN 1 ELSE 0 END) urgentes
            FROM mantenimiento
        """).fetchone())
        conn.close(); return row

    # ==================== GASTOS ====================

    def get_gastos(self, apartamento_id=None, anyo=None):
        conn = self._conn()
        q = """
            SELECT g.*, a.nombre apt_nombre
            FROM gastos g
            LEFT JOIN apartamentos a ON g.apartamento_id = a.id
        """
        conds, params = [], []
        if apartamento_id: conds.append("g.apartamento_id=?"); params.append(apartamento_id)
        if anyo: conds.append("strftime('%Y',g.fecha)=?"); params.append(str(anyo))
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY g.fecha DESC"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        conn.close(); return rows

    def add_gasto(self, d):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO gastos (apartamento_id,descripcion,importe,fecha,categoria,notas) "
            "VALUES (?,?,?,?,?,?)",
            (d.get('apartamento_id'), d['descripcion'], d['importe'],
             d['fecha'], d.get('categoria', 'otro'), d.get('notas', ''))
        )
        conn.commit(); lid = cur.lastrowid; conn.close(); return lid

    def update_gasto(self, id_, d):
        conn = self._conn()
        conn.execute(
            "UPDATE gastos SET apartamento_id=?,descripcion=?,importe=?,fecha=?,categoria=?,notas=? "
            "WHERE id=?",
            (d.get('apartamento_id'), d['descripcion'], d['importe'],
             d['fecha'], d.get('categoria', 'otro'), d.get('notas', ''), id_)
        )
        conn.commit(); conn.close()

    def delete_gasto(self, id_):
        conn = self._conn()
        conn.execute("DELETE FROM gastos WHERE id=?", (id_,))
        conn.commit(); conn.close()

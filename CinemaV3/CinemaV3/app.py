from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
import datetime

import os


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'rap_chieu_phim'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

def load_schema_from_db():
    """Lấy thông tin bảng/cột/khóa chính trực tiếp từ MySQL."""
    schema = {}
    db_name = app.config['MYSQL_DB']
    cur = mysql.connection.cursor()

    try:
        cur.execute(
            """
            SELECT
                TABLE_NAME AS table_name,
                COLUMN_NAME AS column_name
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
            (db_name,)
        )
        column_rows = cur.fetchall()

        cur.execute(
            """
            SELECT
                TABLE_NAME AS table_name,
                COLUMN_NAME AS column_name
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
            (db_name,)
        )
        pk_rows = cur.fetchall()
    finally:
        cur.close()

    for row in column_rows:
        table = row['table_name']
        column = row['column_name']
        schema.setdefault(table, {'pk': None, 'pk_cols': [], 'cols': []})
        schema[table]['cols'].append(column)

    for row in pk_rows:
        table = row['table_name']
        column = row['column_name']
        schema.setdefault(table, {'pk': None, 'pk_cols': [], 'cols': []})
        schema[table]['pk_cols'].append(column)
        if schema[table]['pk'] is None:
            schema[table]['pk'] = column

    for table, meta in schema.items():
        # Nếu bảng không có PK, fallback về cột đầu tiên để giữ tương thích thao tác search/delete.
        if meta['pk'] is None and meta['cols']:
            meta['pk'] = meta['cols'][0]

    return schema


def build_pk_filter(pk_cols, raw_id):
    """Tạo where-clause cho PK đơn hoặc PK ghép (id ghép bằng dấu phẩy)."""
    if len(pk_cols) == 1:
        return f"{pk_cols[0]} = %s", [raw_id]

    parts = [p.strip() for p in str(raw_id).split(',')]
    if len(parts) != len(pk_cols):
        raise ValueError(
            f"Bảng có khóa chính ghép {pk_cols}. Hãy nhập ID theo định dạng: "
            + ", ".join(pk_cols)
            + " (phân tách bằng dấu phẩy)."
        )

    where_clause = ' AND '.join([f"{col} = %s" for col in pk_cols])
    return where_clause, parts

def convert_datetime(obj):
    if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
        return str(obj)
    return obj

@app.route('/')
def index():
    try:
        schema = load_schema_from_db()
        schema_cols = {table: meta['cols'] for table, meta in schema.items()}
        return render_template('index.html', schema_cols=schema_cols, schema_error='')
    except Exception as e:
        return render_template(
            'index.html',
            schema_cols={},
            schema_error=f'Không thể tải schema từ MySQL: {str(e)}'
        )

@app.route('/api', methods=['POST'])
def api():
    data = request.json or {}
    action = data.get('action')
    table = data.get('table')

    try:
        schema = load_schema_from_db()
        if table not in schema:
            return jsonify({'status': 'error', 'msg': f'Bảng không hợp lệ: {table}'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'LỖI schema: {str(e)}'})

    cur = mysql.connection.cursor()
    try:
        # 1. VIEW ALL
        if action == 'view':
            cur.execute(f"SELECT * FROM {table}")
            res = cur.fetchall()
            res = [{k: convert_datetime(v) for k, v in row.items()} for row in res]
            return jsonify({'status': 'success', 'data': res, 'msg': f'Duyệt dữ liệu bảng: {table}'})
            
        # 2. SEARCH BY ID
        if action == 'search':
            val = data.get('id')
            pk_cols = schema[table]['pk_cols'] or [schema[table]['pk']]
            where_clause, where_values = build_pk_filter(pk_cols, val)
            cur.execute(f"SELECT * FROM {table} WHERE {where_clause}", tuple(where_values))
            res = cur.fetchall()
            res = [{k: convert_datetime(v) for k, v in row.items()} for row in res]
            return jsonify({'status': 'success', 'data': res, 'msg': f'Tìm thấy {len(res)} kết quả'})

        # 3. INSERT (THÊM DỮ LIỆU)
        if action == 'insert':
            vals = data.get('values') or [] # Dạng list giá trị theo thứ tự cols
            cols = schema[table]['cols']
            if len(vals) != len(cols):
                return jsonify({'status': 'error', 'msg': 'Số lượng giá trị không khớp với số cột của bảng'})
            placeholders = ', '.join(['%s'] * len(vals))
            sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
            cur.execute(sql, tuple(vals))
            mysql.connection.commit()
            return jsonify({'status': 'success', 'msg': 'Thêm dữ liệu thành công!'})

        # 4. DELETE
        if action == 'delete':
            val = data.get('id')
            pk_cols = schema[table]['pk_cols'] or [schema[table]['pk']]
            where_clause, where_values = build_pk_filter(pk_cols, val)
            cur.execute(f"DELETE FROM {table} WHERE {where_clause}", tuple(where_values))
            mysql.connection.commit()
            return jsonify({'status': 'success', 'msg': 'Đã xóa dữ liệu'})

        return jsonify({'status': 'error', 'msg': f'Action không hợp lệ: {action}'})

    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'LỖI: {str(e)}'})
    finally:
        cur.close()

if __name__ == '__main__':
    app.run(debug=True)
    os.system("pause")
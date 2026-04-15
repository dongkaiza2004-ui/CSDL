import os

folder = "CinemaV3"
os.makedirs(f"{folder}/templates", exist_ok=True)

# --- SERVER CODE (app.py) ---
server_code = """from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
import datetime

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'rap_chieu_phim'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# Cấu hình khóa chính và các cột cho Form Insert
SCHEMA = {
    'Phim': {'pk': 'ma_phim', 'cols': ['ma_phim', 'ten_phim', 'the_loai', 'thoi_luong', 'dao_dien', 'gioi_han_do_tuoi']},
    'PhongChieu': {'pk': 'ma_phong', 'cols': ['ma_phong', 'loai_phong', 'so_luong_ghe', 'tinh_trang_thiet_bi']},
    'Ghe': {'pk': 'ma_ghe', 'cols': ['ma_ghe', 'ma_phong', 'hang', 'cot', 'loai_ghe']},
    'SuatChieu': {'pk': 'ma_suat_chieu', 'cols': ['ma_suat_chieu', 'ma_phim', 'ma_phong', 'thoi_gian_bat_dau', 'ngay_chieu']},
    'KhachHang': {'pk': 'ma_khach_hang', 'cols': ['ma_khach_hang', 'ho_ten', 'so_dien_thoai', 'ngay_sinh']},
    'NhanVien': {'pk': 'ma_nhan_vien', 'cols': ['ma_nhan_vien', 'ten', 'chuc_vu', 'ca_lam_viec']},
    'Ve': {'pk': 'ma_ve', 'cols': ['ma_ve', 'ma_suat_chieu', 'ma_ghe', 'ma_phong', 'ma_khach_hang', 'gia_ve', 'trang_thai']},
    'PhanCong': {'pk': 'ma_nhan_vien', 'cols': ['ma_nhan_vien', 'ma_suat_chieu', 'vai_tro']}
}

def convert_datetime(obj):
    if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
        return str(obj)
    return obj

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    data = request.json
    action = data.get('action')
    table = data.get('table')
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
            pk_col = SCHEMA[table]['pk']
            cur.execute(f"SELECT * FROM {table} WHERE {pk_col} = %s", (val,))
            res = cur.fetchall()
            res = [{k: convert_datetime(v) for k, v in row.items()} for row in res]
            return jsonify({'status': 'success', 'data': res, 'msg': f'Tìm thấy {len(res)} kết quả'})

        # 3. INSERT (THÊM DỮ LIỆU)
        if action == 'insert':
            vals = data.get('values') # Dạng list giá trị theo thứ tự cols
            placeholders = ', '.join(['%s'] * len(vals))
            sql = f"INSERT INTO {table} ({', '.join(SCHEMA[table]['cols'])}) VALUES ({placeholders})"
            cur.execute(sql, tuple(vals))
            mysql.connection.commit()
            return jsonify({'status': 'success', 'msg': 'Thêm dữ liệu thành công!'})

        # 4. DELETE
        if action == 'delete':
            val = data.get('id')
            pk_col = SCHEMA[table]['pk']
            cur.execute(f"DELETE FROM {table} WHERE {pk_col} = %s", (val,))
            mysql.connection.commit()
            return jsonify({'status': 'success', 'msg': 'Đã xóa dữ liệu'})

    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'LỖI: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
"""

# --- UI CODE (index.html) ---
ui_code = """<!DOCTYPE html>
<html>
<head>
    <title>Cinema DB Management Pro</title>
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; margin:0; display: flex; }
        .sidebar { width: 250px; background: #1a1a1a; height: 100vh; border-right: 1px solid #333; padding: 20px; position: fixed; }
        .main { margin-left: 290px; padding: 30px; width: calc(100% - 340px); }
        h3 { color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; }
        .nav-item { padding: 12px; cursor: pointer; border-radius: 6px; margin-bottom: 8px; transition: 0.2s; color: #999; }
        .nav-item:hover { background: #252525; color: #fff; }
        .nav-item.active { background: #333; color: #00ff88; font-weight: bold; border-left: 4px solid #00ff88; }
        .toolbar { background: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 25px; }
        input { background: #000; border: 1px solid #444; color: #00ff88; padding: 10px; border-radius: 5px; outline: none; margin-right: 10px; }
        button { padding: 10px 20px; border-radius: 5px; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn-main { background: #00ff88; color: #000; }
        .btn-main:hover { background: #00cc6e; }
        .btn-outline { background: #333; color: #fff; border: 1px solid #444; }
        .btn-danger { background: #ff4d4d; color: #fff; }
        #status { padding: 15px; border-radius: 8px; margin-bottom: 20px; display: none; font-size: 14px; }
        .success { display: block !important; background: rgba(0, 255, 136, 0.1); border: 1px solid #00ff88; color: #00ff88; }
        .error { display: block !important; background: rgba(255, 77, 77, 0.1); border: 1px solid #ff4d4d; color: #ff4d4d; }
        table { width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 10px; overflow: hidden; }
        th { background: #000; color: #777; padding: 15px; text-align: left; font-size: 12px; border-bottom: 2px solid #333; }
        td { padding: 15px; border-bottom: 1px solid #252525; font-size: 14px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 100; }
        .modal-content { background: #1e1e1e; width: 450px; margin: 100px auto; padding: 30px; border-radius: 10px; border: 1px solid #444; }
        .modal-input { width: 90%; margin-bottom: 15px; display: block; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>Database Tables</h3>
        <div id="nav-list"></div>
    </div>

    <div class="main">
        <h1 id="titleText">Bảng: Phim</h1>
        <div class="toolbar">
            <button class="btn-main" onclick="send('view')">Duyệt Tất Cả (View All)</button>
            <button class="btn-outline" onclick="openInsert()">Thêm Dữ Liệu (Insert)</button>
            <span style="color: #444; margin: 0 15px;">|</span>
            <input id="idInput" placeholder="Nhập mã ID...">
            <button class="btn-outline" onclick="send('search')">Truy Vấn ID</button>
            <button class="btn-danger" onclick="send('delete')">Xóa Dòng</button>
        </div>

        <div id="status"></div>

        <table id="dataTable">
            <thead id="tHead"></thead>
            <tbody id="tBody"></tbody>
        </table>
    </div>

    <!-- Modal Thêm Dữ Liệu -->
    <div id="insertModal" class="modal">
        <div class="modal-content">
            <h2 id="modalTitle" style="color: #00ff88; margin-top: 0;">Insert Data</h2>
            <div id="formFields"></div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn-outline" onclick="closeInsert()">Hủy</button>
                <button class="btn-main" onclick="doInsert()">Lưu Lại</button>
            </div>
        </div>
    </div>

    <script>
        const SCHEMA = {
            'Phim': ['ma_phim', 'ten_phim', 'the_loai', 'thoi_luong', 'dao_dien', 'gioi_han_do_tuoi'],
            'PhongChieu': ['ma_phong', 'loai_phong', 'so_luong_ghe', 'tinh_trang_thiet_bi'],
            'Ghe': ['ma_ghe', 'ma_phong', 'hang', 'cot', 'loai_ghe'],
            'SuatChieu': ['ma_suat_chieu', 'ma_phim', 'ma_phong', 'thoi_gian_bat_dau', 'ngay_chieu'],
            'KhachHang': ['ma_khach_hang', 'ho_ten', 'so_dien_thoai', 'ngay_sinh'],
            'NhanVien': ['ma_nhan_vien', 'ten', 'chuc_vu', 'ca_lam_viec'],
            'Ve': ['ma_ve', 'ma_suat_chieu', 'ma_ghe', 'ma_phong', 'ma_khach_hang', 'gia_ve', 'trang_thai'],
            'PhanCong': ['ma_nhan_vien', 'ma_suat_chieu', 'vai_tro']
        };

        let currentTable = 'Phim';

        // Khởi tạo menu
        const nav = document.getElementById('nav-list');
        Object.keys(SCHEMA).forEach((table, idx) => {
            let div = document.createElement('div');
            div.className = 'nav-item' + (table === 'Phim' ? ' active' : '');
            div.innerText = (idx + 1) + '. ' + table;
            div.onclick = () => {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                div.classList.add('active');
                currentTable = table;
                document.getElementById('titleText').innerText = 'Bảng: ' + table;
                document.getElementById('tBody').innerHTML = '';
            };
            nav.appendChild(div);
        });

        async function send(action, extra = {}) {
            let id = document.getElementById('idInput').value;
            let response = await fetch('/api', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: action, table: currentTable, id: id, ...extra })
            });
            let res = await response.json();
            let statusDiv = document.getElementById('status');
            statusDiv.innerText = res.msg;
            statusDiv.className = res.status == 'success' ? 'success' : 'error';
            if(res.data) render(res.data);
            if(action == 'delete' || action == 'insert') if(res.status == 'success') send('view');
        }

        function render(data) {
            let h = document.getElementById('tHead'), b = document.getElementById('tBody');
            h.innerHTML = ""; b.innerHTML = "";
            if(data.length > 0) {
                let cols = Object.keys(data[0]);
                h.innerHTML = "<tr>" + cols.map(c => `<th>${c}</th>`).join('') + "</tr>";
                b.innerHTML = data.map(row => "<tr>" + cols.map(c => `<td>${row[c]}</td>`).join('') + "</tr>").join('');
            }
        }

        function openInsert() {
            document.getElementById('modalTitle').innerText = 'Thêm dòng mới: ' + currentTable;
            let fields = document.getElementById('formFields');
            fields.innerHTML = SCHEMA[currentTable].map(col => `<input class="modal-input" id="field_${col}" placeholder="${col}">`).join('');
            document.getElementById('insertModal').style.display = 'block';
        }

        function closeInsert() { document.getElementById('insertModal').style.display = 'none'; }

        function doInsert() {
            let values = SCHEMA[currentTable].map(col => document.getElementById('field_' + col).value);
            send('insert', { values: values });
            closeInsert();
        }
    </script>
</body>
</html>
"""

with open(f"{folder}/app.py", "w", encoding="utf-8") as f: f.write(server_code)
with open(f"{folder}/templates/index.html", "w", encoding="utf-8") as f: f.write(ui_code)
print("--- ĐÃ TẠO XONG PHIÊN BẢN V3 ---")
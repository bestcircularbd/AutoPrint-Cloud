import os
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'cloud_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('cloud.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id TEXT, filename TEXT, status TEXT)''')
    conn.commit()
    conn.close()
init_db()

@app.route('/api/upload_job', methods=['POST'])
def upload_job():
    shop_id = request.form.get('shop_id')
    file = request.files['file']
    if file:
        filename = f"{shop_id}_{secure_filename(file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        conn = sqlite3.connect('cloud.db')
        conn.execute("INSERT INTO jobs (shop_id, filename, status) VALUES (?, ?, 'pending')", (shop_id, filename))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/admin')
def super_admin():
    conn = sqlite3.connect('cloud.db')
    jobs = conn.execute("SELECT * FROM jobs WHERE status='pending'").fetchall()
    conn.close()
    return render_template('cloud_admin.html', jobs=jobs)

@app.route('/approve/<int:job_id>', methods=['POST'])
def approve_job(job_id):
    conn = sqlite3.connect('cloud.db')
    conn.execute("UPDATE jobs SET status='approved' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()
    return "Approved"

@app.route('/api/check_jobs/<shop_id>', methods=['GET'])
def check_jobs(shop_id):
    conn = sqlite3.connect('cloud.db')
    job = conn.execute("SELECT * FROM jobs WHERE shop_id=? AND status='approved' LIMIT 1", (shop_id,)).fetchone()
    if job:
        conn.execute("UPDATE jobs SET status='printing' WHERE id=?", (job[0],))
        conn.commit()
        conn.close()
        return jsonify({"has_job": True, "job_id": job[0], "filename": job[2]})
    conn.close()
    return jsonify({"has_job": False})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/job_done/<int:job_id>', methods=['POST'])
def job_done(job_id):
    conn = sqlite3.connect('cloud.db')
    conn.execute("UPDATE jobs SET status='completed' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "done"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
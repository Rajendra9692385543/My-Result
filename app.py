from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import pandas as pd
import os

app = Flask(__name__)


DB_FILE = 'results.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from flask import send_from_directory

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory('uploads', filename, as_attachment=True)

# ==========================
# DB INIT
# ==========================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Main results table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT,
            name TEXT,
            subject_code TEXT,
            subject_name TEXT,
            type TEXT,
            credits TEXT,
            grade TEXT,
            semester TEXT,
            school TEXT,
            branch TEXT,
            academic_year TEXT,
            UNIQUE(reg_no, subject_code)
        )
    ''')

    # Ensure columns exist if DB already created earlier
    try:
        cur.execute("ALTER TABLE results ADD COLUMN school TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE results ADD COLUMN branch TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE results ADD COLUMN academic_year TEXT")
    except sqlite3.OperationalError:
        pass

    # Upload log table (no academic_year)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            upload_type TEXT,
            school TEXT,
            branch TEXT,
            semester TEXT,
            academic_year TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

init_db()


# ==========================
# School Mapping
# ==========================
# Map of School to their respective Branches (move outside route)
school_branch_map = {
    "School of Engineering and Technology": [
        "Computer Science and Engineering",
        "Mechanical Engineering",
        "Electrical and Electronics Engineering",
        "Civil Engineering",
        "Agricultural Engineering",
        "Biotechnology Engineering",
        "Aerospace Engineering",
        "Bachelor of Computer Application (BCA)"
    ],
    "M.S. Swaminathan School of Agriculture": ["Agronomy", "Horticulture", "Soil Science"],
    "School of Management": ["BBA", "MBA"],
    "School of Fisheries": ["Fisheries Science"],
    "School of Vocational Education and Training": ["Vocational Training"],
    "School of Applied Sciences": ["Physics", "Chemistry", "Mathematics"],
    "School of Agriculture & Bio-Engineering": ["Bio-Engineering"],
    "School of Veterinary and Animal Sciences": ["Veterinary Science"],
    "School of Nursing": ["Nursing"]
}

# ==========================
# Helpers
# ==========================
def calculate_grade_point(grade):
    mapping = {'O': 10, 'E': 9, 'A': 8, 'B': 7, 'C': 6, 'D': 5,'F': 0, 'S': 0}
    return mapping.get(grade.upper(), 0)

def calculate_gpa(records):
    total_credits = 0
    weighted_points = 0
    for row in records:
        try:
            credits = sum(map(float, row['credits'].split('+'))) if '+' in row['credits'] else float(row['credits'])
            points = calculate_grade_point(row['grade'])
            total_credits += credits
            weighted_points += points * credits
        except:
            continue
    return round(weighted_points / total_credits, 2) if total_credits else 0.0

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================
# Routes
# ==========================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    reg_no = request.form['reg_no'].strip()
    semester = request.form['semester'].strip()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get current semester result
    cur.execute("SELECT * FROM results WHERE reg_no = ? AND semester = ?", (reg_no, semester))
    semester_records = cur.fetchall()

    # Get all semesters for CGPA
    cur.execute("SELECT * FROM results WHERE reg_no = ?", (reg_no,))
    all_records = cur.fetchall()

    if not semester_records:
        return render_template('result.html', name="Not Found", reg_no=reg_no, semester=semester,
                               sgpa=0, cgpa=0, subjects=[], chart_data=[],
                               school="-", branch="-", academic_year="-")

    name = semester_records[0]['name']
    school = semester_records[0]['school']
    branch = semester_records[0]['branch']
    academic_year = semester_records[0]['academic_year']

    sgpa = calculate_gpa(semester_records)
    cgpa = calculate_gpa(all_records)

    # Prepare CGPA chart data across semesters
    cur.execute("SELECT DISTINCT semester FROM results WHERE reg_no = ? ORDER BY semester", (reg_no,))
    semesters = [row[0] for row in cur.fetchall()]
    chart_data = []

    for sem in semesters:
        cur.execute("SELECT * FROM results WHERE reg_no = ? AND semester = ?", (reg_no, sem))
        rows = cur.fetchall()
        gpa = calculate_gpa(rows)
        chart_data.append({"semester": sem, "cgpa": gpa})

    conn.close()

    return render_template('result.html',
                           name=name,
                           reg_no=reg_no,
                           semester=semester,
                           sgpa=sgpa,
                           cgpa=cgpa,
                           subjects=semester_records,
                           chart_data=chart_data,
                           school=school,
                           branch=branch,
                           academic_year=academic_year)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))  # ✅ Redirect to dashboard after success

        return render_template('admin_login.html', error="Oops! Wrong username or password.")

    return render_template('admin_login.html')


from datetime import datetime

def generate_academic_years(start_year=2020):
    current_year = datetime.now().year
    # Include next academic year if past June
    if datetime.now().month > 6:
        current_year += 1
    return [f"{y}-{y + 1}" for y in range(start_year, current_year)]

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # School and Branch Mapping
    school_branch_map = {
        "School of Engineering and Technology": [
            "Computer Science and Engineering",
            "Mechanical Engineering",
            "Electrical and Electronics Engineering",
            "Civil Engineering",
            "Agricultural Engineering",
            "Biotechnology Engineering",
            "Aerospace Engineering",
            "Bachelor of Computer Application (BCA)"
        ],
        "M.S. Swaminathan School of Agriculture": [
            "Agronomy", "Horticulture", "Soil Science"
        ],
        "School of Management": ["BBA", "MBA"],
        "School of Fisheries": ["Fisheries Science"],
        "School of Vocational Education and Training": ["Vocational Training"],
        "School of Applied Sciences": ["Physics", "Chemistry", "Mathematics"],
        "School of Agriculture & Bio-Engineering": ["Bio-Engineering"],
        "School of Veterinary and Animal Sciences": ["Veterinary Science"],
        "School of Nursing": ["Nursing"]
    }

    # Generate academic year options
    academic_years = generate_academic_years()

    # Fetch uploaded file logs
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM uploads ORDER BY timestamp DESC")
    uploads = cur.fetchall()
    conn.close()

    return render_template("admin_dashboard.html",
                           message=None,
                           schoolBranchMap=school_branch_map,
                           uploads=uploads,
                           academic_years=academic_years)

@app.route('/admin/upload_insert', methods=['POST'])
def upload_insert():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    file = request.files.get('file')
    school = request.form.get('school')
    branch = request.form.get('branch')
    semester = request.form.get('semester')
    academic_year = request.form.get('academic_year')

    if not file or not allowed_file(file.filename):
        return render_template("admin_dashboard.html",
                               message="Please upload a valid .xlsx file.",
                               schoolBranchMap=school_branch_map)

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    df = pd.read_excel(filepath)
    df.fillna('', inplace=True)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        reg_no = str(row['Reg_No']).strip()
        name = str(row['Name']).strip()
        subject_code = str(row['Subject_Code']).strip()
        subject_name = str(row['Subject_Name']).strip()
        type_ = str(row['Type']).strip()
        credits = str(row['Credits']).strip()
        grade = str(row['Grade']).strip()

        cur.execute("""
            INSERT OR IGNORE INTO results 
            (reg_no, name, subject_code, subject_name, type, credits, grade, semester, school, branch, academic_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reg_no, name, subject_code, subject_name, type_, credits, grade, semester, school, branch, academic_year))
        inserted += 1

    # Log the file upload
    cur.execute("""
        INSERT INTO uploads (filename, upload_type, school, branch, semester, academic_year)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (filename, 'Sem Result', school, branch, semester, academic_year))

    conn.commit()
    conn.close()

    flash(f"{inserted} rows inserted successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/upload_update', methods=['POST'])
def upload_update():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    file = request.files.get('file')

    if not file or not allowed_file(file.filename):
        return render_template("admin_dashboard.html", message="Please upload a valid .xlsx file.", schoolBranchMap=school_branch_map)

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    df = pd.read_excel(filepath)
    df.fillna('', inplace=True)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    updated = 0

    for _, row in df.iterrows():
        reg_no = str(row['Reg_No']).strip()
        subject_code = str(row['Subject_Code']).strip()
        name = str(row['Name']).strip()
        subject_name = str(row['Subject_Name']).strip()
        type_ = str(row['Type']).strip()
        credits = str(row['Credits']).strip()
        grade = str(row['Grade']).strip()

        cur.execute("""
            UPDATE results
            SET name = ?, subject_name = ?, type = ?, credits = ?, grade = ?
            WHERE reg_no = ? AND subject_code = ?
        """, (name, subject_name, type_, credits, grade, reg_no, subject_code))
        updated += 1

    # Log the update
    cur.execute("""
        INSERT INTO uploads (filename, upload_type)
        VALUES (?, 'EOD')
    """, (filename,))

    conn.commit()
    conn.close()

    flash(f"{updated} rows updated successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/get_semesters')
def get_semesters():
    reg_no = request.args.get('reg_no', '').strip()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT semester FROM results WHERE reg_no = ?", (reg_no,))
    semesters = [row[0] for row in cur.fetchall()]
    conn.close()
    return {'semesters': semesters}

@app.route('/topper', methods=['GET', 'POST'])
def topper():
    academic_years = [f"{y}-{y+1}" for y in range(2020, datetime.now().year + 1)]

    if request.method == 'POST':
        school = request.form['school']
        branch = request.form['branch']
        semester = request.form['semester']
        academic_year = request.form['academic_year']

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Step 1: Get all students in that school, branch, semester, academic year
        cur.execute("""
            SELECT DISTINCT reg_no, name, school, branch, semester, academic_year
            FROM results
            WHERE school = ? AND branch = ? AND semester = ? AND academic_year = ?
        """, (school, branch, semester, academic_year))

        students = cur.fetchall()
        toppers = []

        for student in students:
            reg_no = student['reg_no']

            # SGPA for this semester
            cur.execute("""
                SELECT grade FROM results 
                WHERE reg_no = ? AND semester = ?
            """, (reg_no, semester))
            sgpa_grades = [row['grade'] for row in cur.fetchall()]

            sgpa = calculate_gpa_from_grades(sgpa_grades)

            # CGPA for all semesters
            cur.execute("""
                SELECT grade FROM results 
                WHERE reg_no = ?
            """, (reg_no,))
            cgpa_grades = [row['grade'] for row in cur.fetchall()]

            cgpa = calculate_gpa_from_grades(cgpa_grades)

            toppers.append({
                "reg_no": student['reg_no'],
                "name": student['name'],
                "school": student['school'],
                "branch": student['branch'],
                "semester": student['semester'],
                "academic_year": student['academic_year'],
                "sgpa": round(sgpa, 2),
                "cgpa": round(cgpa, 2)
            })

        # Sort by SGPA descending, then CGPA descending
        toppers.sort(key=lambda x: (-x['sgpa'], -x['cgpa']))

        # Limit to top 10
        toppers = toppers[:10]

        conn.close()

        return render_template("topper.html", 
                               schoolBranchMap=school_branch_map, 
                               academic_years=academic_years,
                               toppers=toppers,
                               form_data=request.form)

    return render_template("topper.html", 
                           schoolBranchMap=school_branch_map,
                           academic_years=academic_years,
                           toppers=None,
                           form_data={})
def calculate_gpa_from_grades(grades):
    grade_map = {
        'O': 10, 'E': 9, 'A': 8, 'B': 7, 'C': 6, 'D': 5, 'F': 0
    }
    points = [grade_map.get(g, 0) for g in grades]
    return sum(points) / len(points) if points else 0

if __name__ == '__main__':
    app.run()



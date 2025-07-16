from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import pandas as pd
from supabase import create_client, Client

# ==========================
# Supabase Config
# ==========================
SUPABASE_URL = "https://xsnktkaofijftripytij.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhzbmt0a2FvZmlqZnRyaXB5dGlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2NDM2MDAsImV4cCI6MjA2ODIxOTYwMH0.NKo7WAeN7ssRg_5LceDABBaUJF-jAEjxBrCjKtoxvgg"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# Flask Setup
# ==========================
app = Flask(__name__)
app.secret_key = 'secret_key_here'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================
# File Serving Route
# ==========================
@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory('uploads', filename, as_attachment=True)

# ==========================
# School Mapping
# ==========================
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
    mapping = {'O': 10, 'E': 9, 'A': 8, 'B': 7, 'C': 6, 'D': 5, 'F': 0, 'S': 0}
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

    # Get current semester result
    response = supabase.table("results").select("*").eq("reg_no", reg_no).eq("semester", semester).execute()
    semester_records = response.data if response.data else []

    # Get all semesters for CGPA
    response_all = supabase.table("results").select("*").eq("reg_no", reg_no).execute()
    all_records = response_all.data if response_all.data else []

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

    # Get list of semesters
    semesters_resp = supabase.table("results") \
        .select("semester") \
        .eq("reg_no", reg_no) \
        .order("semester", desc=False) \
        .execute()

    semesters = list({row["semester"] for row in semesters_resp.data})

    chart_data = []
    for sem in semesters:
        response = supabase.table("results").select("*").eq("reg_no", reg_no).eq("semester", sem).execute()
        rows = response.data
        gpa = calculate_gpa(rows)
        chart_data.append({"semester": sem, "cgpa": gpa})

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

    # ✅ Fetch uploads from Supabase
    try:
        response = supabase.table("uploads").select("*").order("timestamp", desc=True).execute()
        uploads = response.data if response.data else []
    except Exception as e:
        uploads = []
        flash(f"Error fetching uploads: {e}")

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

    errors = []

    # ✅ Build list of (reg_no, subject_code) for entire sheet
    keys = [
        (str(row.get('Reg_No', '')).strip(), str(row.get('Subject_Code', '')).strip())
        for _, row in df.iterrows()
        if str(row.get('Reg_No', '')).strip() and str(row.get('Subject_Code', '')).strip()
    ]

    # ✅ Get all existing keys from Supabase in one query
    try:
        existing_resp = supabase.table("results").select("reg_no, subject_code").in_(
            "reg_no", [k[0] for k in keys]
        ).execute()

        existing_keys = set(
            (row['reg_no'], row['subject_code']) for row in existing_resp.data
        )
    except Exception as e:
        flash(f"Failed to fetch existing records: {e}")
        return redirect(url_for('admin_dashboard'))

    # ✅ Prepare list of new rows to insert
    new_rows = []
    for _, row in df.iterrows():
        reg_no = str(row.get('Reg_No', '')).strip()
        subject_code = str(row.get('Subject_Code', '')).strip()

        if not reg_no or not subject_code:
            continue  # Skip invalid rows

        if (reg_no, subject_code) in existing_keys:
            continue  # Already exists

        new_rows.append({
            "reg_no": reg_no,
            "name": str(row.get('Name', '')).strip(),
            "subject_code": subject_code,
            "subject_name": str(row.get('Subject_Name', '')).strip(),
            "type": str(row.get('Type', '')).strip(),
            "credits": str(row.get('Credits', '')).strip(),
            "grade": str(row.get('Grade', '')).strip(),
            "semester": semester,
            "school": school,
            "branch": branch,
            "academic_year": academic_year
        })

    inserted = 0

    # ✅ Insert in bulk if any new rows
    if new_rows:
        try:
            insert_resp = supabase.table("results").insert(new_rows).execute()
            inserted = len(new_rows)
        except Exception as e:
            errors.append(f"Insertion failed: {e}")

    # ✅ Log the upload
    try:
        supabase.table("uploads").insert({
            "filename": filename,
            "upload_type": "Sem Result",
            "school": school,
            "branch": branch,
            "semester": semester,
            "academic_year": academic_year
        }).execute()
    except Exception as e:
        errors.append(f"Upload log failed: {e}")

    # ✅ Flash messages
    if inserted:
        flash(f"{inserted} rows inserted successfully.")
    else:
        flash("⚠️ No new records inserted.")

    if errors:
        flash("Some errors occurred: " + "; ".join(errors))

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

    updated = 0
    errors = []

    for _, row in df.iterrows():
        try:
            reg_no = str(row['Reg_No']).strip()
            subject_code = str(row['Subject_Code']).strip()
            name = str(row['Name']).strip()
            subject_name = str(row['Subject_Name']).strip()
            type_ = str(row['Type']).strip()
            credits = str(row['Credits']).strip()
            grade = str(row['Grade']).strip()

            # Get the row to update
            match_result = supabase.table("results").select("id").match({
                "reg_no": reg_no,
                "subject_code": subject_code
            }).execute()

            if match_result.data:
                record_id = match_result.data[0]['id']
                supabase.table("results").update({
                    "name": name,
                    "subject_name": subject_name,
                    "type": type_,
                    "credits": credits,
                    "grade": grade
                }).eq("id", record_id).execute()
                updated += 1
        except Exception as e:
            errors.append(str(e))

    # Log the update
    try:
        supabase.table("uploads").insert({
            "filename": filename,
            "upload_type": "EOD"
        }).execute()
    except Exception as e:
        errors.append(f"Upload log failed: {e}")

    if updated:
        flash(f"{updated} rows updated successfully.")
    else:
        flash("No matching records were found to update.")

    if errors:
        flash("Some errors occurred: " + "; ".join(errors))

    return redirect(url_for('admin_dashboard'))

@app.route('/get_semesters')
def get_semesters():
    reg_no = request.args.get('reg_no', '').strip()

    try:
        response = supabase.table("results") \
            .select("semester") \
            .eq("reg_no", reg_no) \
            .execute()

        # Extract distinct semesters
        semesters = list({row['semester'] for row in response.data if row.get('semester')})

        # Optional: sort semesters if needed
        semesters.sort()

        return {'semesters': semesters}

    except Exception as e:
        return {'error': str(e), 'semesters': []}

from datetime import datetime

@app.route('/topper', methods=['GET', 'POST'])
def topper():
    academic_years = [f"{y}-{y+1}" for y in range(2020, datetime.now().year + 1)]

    if request.method == 'POST':
        school = request.form['school']
        branch = request.form['branch']
        semester = request.form['semester']
        academic_year = request.form['academic_year']

        # Step 1: Fetch all unique students from Supabase
        response = supabase.table("results") \
            .select("reg_no, name, school, branch, semester, academic_year") \
            .eq("school", school) \
            .eq("branch", branch) \
            .eq("semester", semester) \
            .eq("academic_year", academic_year) \
            .execute()

        students = response.data
        toppers = []

        for student in students:
            reg_no = student['reg_no']

            # Get SGPA: All grades for this reg_no & semester
            sgpa_response = supabase.table("results") \
                .select("grade") \
                .eq("reg_no", reg_no) \
                .eq("semester", semester) \
                .execute()
            sgpa_grades = [row['grade'] for row in sgpa_response.data]

            # Get CGPA: All grades for this reg_no (all semesters)
            cgpa_response = supabase.table("results") \
                .select("grade") \
                .eq("reg_no", reg_no) \
                .execute()
            cgpa_grades = [row['grade'] for row in cgpa_response.data]

            # GPA Calculations
            sgpa = calculate_gpa_from_grades(sgpa_grades)
            cgpa = calculate_gpa_from_grades(cgpa_grades)

            toppers.append({
                "reg_no": reg_no,
                "name": student['name'],
                "school": student['school'],
                "branch": student['branch'],
                "semester": semester,
                "academic_year": academic_year,
                "sgpa": round(sgpa, 2),
                "cgpa": round(cgpa, 2)
            })

        # Sort: first by SGPA (desc), then by CGPA (desc)
        toppers.sort(key=lambda x: (-x['sgpa'], -x['cgpa']))

        # Limit to Top 10
        toppers = toppers[:10]

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
        'O': 10, 'E': 9, 'A': 8, 'B': 7, 'C': 6, 'D': 5, 'F': 0, 'S': 0
    }
    points = []
    for grade in grades:
        grade = grade.strip().upper()
        if grade in grade_map:
            points.append(grade_map[grade])
    return round(sum(points) / len(points), 2) if points else 0.0

if __name__ == '__main__':
    app.run(debug=True)

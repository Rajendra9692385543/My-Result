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
# School → Branch Mapping
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

# ==========================
# School → Program Mapping
# ==========================
school_program_map = {
    "School of Engineering and Technology": ["BTech", "BCA", "Diploma"],
    "M.S. Swaminathan School of Agriculture": ["BSc AG"],
    "School of Management": ["BBA", "MBA"],
    "School of Fisheries": ["BSc Fisheries"],
    "School of Vocational Education and Training": ["Diploma"],
    "School of Applied Sciences": ["BSc"],
    "School of Agriculture & Bio-Engineering": ["BTech Bio", "BSc Bio"],
    "School of Veterinary and Animal Sciences": ["BVSc"],
    "School of Nursing": ["BSc Nursing"]
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

from werkzeug.security import check_password_hash

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("❌ Email and password are required.")
            return redirect(url_for('admin_login'))

        try:
            # Fetch admin data
            result = supabase.table("admin_users").select("*").eq("email", email).execute()
            admin_data = result.data

            if not admin_data:
                flash("⚠️ No admin found with that email.")
                return redirect(url_for('admin_login'))

            admin = admin_data[0]

            # ✅ Compare password (plain text check or hashed check)
            if password != admin['password']:
                # Use check_password_hash(admin['password'], password) if hashed
                flash("❌ Incorrect password.")
                return redirect(url_for('admin_login'))

            # ✅ Login success
            session['admin'] = True
            session['admin_email'] = email
            session['admin_role'] = admin.get('role', 'admin')

            flash("✅ Login successful!")
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            flash(f"❌ Login failed: {e}")
            return redirect(url_for('admin_login'))

    return render_template("admin_login_password.html")

from werkzeug.security import generate_password_hash

@app.route('/admin/manage-admins', methods=['GET', 'POST'])
def manage_admins():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Add new admin (POST)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("⚠️ Email and password are required.")
            return redirect(url_for('manage_admins'))

        try:
            # Check if admin already exists
            exists = supabase.table("admin_users").select("email").eq("email", email).execute()
            if exists.data:
                flash("⚠️ This email is already an admin.")
            else:
                hashed_password = generate_password_hash(password)
                supabase.table("admin_users").insert({
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "password": hashed_password
                }).execute()
                flash(f"✅ Admin '{email}' added successfully.")
        except Exception as e:
            flash(f"❌ Failed to add admin: {e}")

        return redirect(url_for('manage_admins'))

    # Display all admins (GET)
    try:
        admins = supabase.table("admin_users") \
                         .select("*") \
                         .order("created_at", desc=True) \
                         .execute().data
    except Exception as e:
        admins = []
        flash(f"❌ Failed to fetch admins: {e}")

    return render_template("manage_admins.html", admins=admins)

from datetime import datetime

@app.route('/admin/add-admin', methods=['POST'])
def add_admin():
    if 'admin' not in session or session.get('admin_role') != 'superadmin':
        flash("Only superadmins can add new admins.")
        return redirect(url_for('admin_dashboard'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '').strip()  # Optional if you want password too

    if not email or not password:
        flash("⚠️ Email and Password are required.")
        return redirect(url_for('manage_admins'))

    try:
        existing = supabase.table("admin_users").select("email").eq("email", email).execute()
        if existing.data:
            flash("⚠️ This email is already an admin.")
        else:
            supabase.table("admin_users").insert({
                "name": name,
                "email": email,
                "phone": phone,
                "password": password,
                "role": "admin",
                "created_at": datetime.utcnow().isoformat()  # Ensures created_at is filled
            }).execute()
            flash(f"✅ Admin '{email}' added.")
    except Exception as e:
        flash(f"❌ Failed to add admin: {e}")

    return redirect(url_for('manage_admins'))

@app.route('/admin/delete-admin', methods=['POST'])
def delete_admin():
    if 'admin' not in session or session.get('admin_role') != 'superadmin':
        flash("Only superadmins can delete admins.")
        return redirect(url_for('admin_dashboard'))

    email = request.form.get('email')
    if not email:
        flash("⚠️ Email is required.")
        return redirect(url_for('manage_admins'))

    try:
        supabase.table("admin_users").delete().eq("email", email).execute()
        flash(f"✅ Admin '{email}' deleted.")
    except Exception as e:
        flash(f"❌ Failed to delete admin: {e}")

    return redirect(url_for('manage_admins'))

#===========================
#Manage Basket Subjects
#===========================
@app.route('/admin/manage-basket', methods=['GET'])
def manage_basket():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Get filters from query parameters (if any)
    selected_program = request.args.get("program", "").strip()
    selected_branch = request.args.get("branch", "").strip()
    selected_basket = request.args.get("basket", "").strip()

    try:
        # Build Supabase filter query dynamically
        query = supabase.table("cbcs_basket").select("*")

        if selected_program:
            query = query.eq("program", selected_program)
        if selected_branch:
            query = query.eq("branch", selected_branch)
        if selected_basket:
            query = query.eq("basket", selected_basket)

        query = query.order("subject_code")
        subjects = query.execute().data

    except Exception as e:
        subjects = []
        flash(f"❌ Failed to load subjects: {e}")

    # Distinct values for dropdowns
    try:
        all_subjects = supabase.table("cbcs_basket").select("program, branch, basket").execute().data
        programs = sorted({row["program"] for row in all_subjects if row["program"]})
        branches = sorted({row["branch"] for row in all_subjects if row["branch"]})
        baskets = sorted({row["basket"] for row in all_subjects if row["basket"]})
    except:
        programs, branches, baskets = [], [], []

    return render_template("manage_basket.html",
                           subjects=subjects,
                           programs=programs,
                           branches=branches,
                           baskets=baskets,
                           selected_program=selected_program,
                           selected_branch=selected_branch,
                           selected_basket=selected_basket)

@app.route('/admin/add-subject', methods=['POST'])
def add_subject():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Extract and clean form data
    subject_code = request.form.get("subject_code", "").strip().upper()
    subject_name = request.form.get("subject_name", "").strip()
    credits = request.form.get("credits", "").strip()
    basket = request.form.get("basket", "").strip()
    program = request.form.get("program", "").strip()
    branch = request.form.get("branch", "").strip()

    # Basic validation
    if not subject_code or not subject_name or not credits or not program or not branch or not basket:
        flash("⚠️ All fields are required.")
        return redirect(url_for('manage_basket'))

    try:
        credits = float(credits)
    except ValueError:
        flash("⚠️ Credits must be a valid number.")
        return redirect(url_for('manage_basket'))

    try:
        # Check if the exact subject already exists
        existing = supabase.table("cbcs_basket").select("id").match({
            "subject_code": subject_code,
            "program": program,
            "branch": branch,
            "basket": basket
        }).execute()

        if existing.data:
            flash(f"⚠️ This subject already exists in the selected basket for this branch & program.")
        else:
            supabase.table("cbcs_basket").insert({
                "subject_code": subject_code,
                "subject_name": subject_name,
                "credits": credits,
                "basket": basket,
                "program": program,
                "branch": branch
            }).execute()
            flash(f"✅ Subject '{subject_code}' added.")
    except Exception as e:
        flash(f"❌ Failed to add subject: {e}")

    return redirect(url_for('manage_basket'))

@app.route('/admin/update-subject', methods=['POST'])
def update_subject():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    subject_code = request.form.get("subject_code", "").strip().upper()
    if not subject_code:
        flash("Subject code is required for update.")
        return redirect(url_for('manage_basket'))

    updates = {}
    if request.form.get("subject_name"):
        updates["subject_name"] = request.form["subject_name"].strip()
    if request.form.get("credits"):
        try:
            updates["credits"] = float(request.form["credits"])
        except:
            flash("Invalid credits.")
            return redirect(url_for('manage_basket'))
    if request.form.get("basket"):
        updates["basket"] = request.form["basket"].strip()

    if not updates:
        flash("No updates provided.")
        return redirect(url_for('manage_basket'))

    try:
        exists = supabase.table("cbcs_basket").select("id").eq("subject_code", subject_code).execute()
        if not exists.data:
            flash("❌ Subject not found.")
        else:
            subject_id = exists.data[0]["id"]
            supabase.table("cbcs_basket").update(updates).eq("id", subject_id).execute()
            flash(f"✅ Subject '{subject_code}' updated.")
    except Exception as e:
        flash(f"❌ Failed to update subject: {e}")

    return redirect(url_for('manage_basket'))

import pandas as pd

@app.route('/admin/upload-subjects', methods=['POST'])
def upload_subjects():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    file = request.files.get("file")
    if not file or not file.filename.endswith(".xlsx"):
        flash("Please upload a valid .xlsx file.")
        return redirect(url_for('manage_basket'))

    try:
        df = pd.read_excel(file)
        df.fillna('', inplace=True)

        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            subject_code = str(row.get("subject_code", "")).strip().upper()
            program = str(row.get("program", "")).strip()
            branch = str(row.get("branch", "")).strip()
            basket = str(row.get("basket", "")).strip()
            subject_name = str(row.get("subject_name", "")).strip()
            credits = str(row.get("credits", "")).strip()

            # Skip invalid
            if not all([subject_code, program, branch, basket, subject_name, credits]):
                skipped += 1
                continue

            # Check if subject already exists
            exists = supabase.table("cbcs_basket").select("id") \
                .eq("subject_code", subject_code) \
                .eq("program", program) \
                .eq("branch", branch).execute()

            if exists.data:
                skipped += 1
                continue

            supabase.table("cbcs_basket").insert({
                "subject_code": subject_code,
                "subject_name": subject_name,
                "credits": credits,
                "basket": basket,
                "program": program,
                "branch": branch
            }).execute()
            inserted += 1

        flash(f"✅ {inserted} subjects added. 🚫 {skipped} skipped (duplicates or incomplete).")
    except Exception as e:
        flash(f"❌ Upload failed: {e}")

    return redirect(url_for('manage_basket'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_email', None)
    session.pop('admin_role', None)
    flash("You have been logged out.")
    return redirect(url_for('admin_login'))

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

    # ==========================
    # School → Branch Mapping
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

    # ==========================
    # School → Program Mapping
    # ==========================
    school_program_map = {
        "School of Engineering and Technology": ["BTech", "BCA", "Diploma"],
        "M.S. Swaminathan School of Agriculture": ["BSc AG"],
        "School of Management": ["BBA", "MBA"],
        "School of Fisheries": ["BSc Fisheries"],
        "School of Vocational Education and Training": ["Diploma"],
        "School of Applied Sciences": ["BSc"],
        "School of Agriculture & Bio-Engineering": ["BTech Bio", "BSc Bio"],
        "School of Veterinary and Animal Sciences": ["BVSc"],
        "School of Nursing": ["BSc Nursing"]
    }

    # ✅ Academic years list
    academic_years = generate_academic_years()

    # ✅ Fetch uploaded result file records
    try:
        response = supabase.table("uploads").select("*").order("timestamp", desc=True).execute()
        uploads = response.data if response.data else []
    except Exception as e:
        uploads = []
        flash(f"Error fetching uploads: {e}")

    return render_template(
        "admin_dashboard.html",
        message=None,
        schoolBranchMap=school_branch_map,
        schoolProgramMap=school_program_map,
        uploads=uploads,
        academic_years=academic_years
    )


@app.route('/admin/upload_insert', methods=['POST'])
def upload_insert():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    file = request.files.get('file')
    school = request.form.get('school')
    branch = request.form.get('branch')
    semester = request.form.get('semester')
    academic_year = request.form.get('academic_year')
    program = request.form.get('program')

    if not file or not allowed_file(file.filename):
        flash("Please upload a valid .xlsx file.")
        return redirect(url_for('admin_dashboard'))

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    df = pd.read_excel(filepath)
    df.fillna('', inplace=True)

    new_rows = []
    errors = []

    for _, row in df.iterrows():
        reg_no = str(row.get('Reg_No', '')).strip()
        subject_code = str(row.get('Subject_Code', '')).strip()

        if not reg_no or not subject_code:
            continue

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
            "academic_year": academic_year,
            "program": program
        })

    inserted = 0
    if new_rows:
        try:
            # You can consider chunking if the file is large
            supabase.table("results").insert(new_rows).execute()
            inserted = len(new_rows)
        except Exception as e:
            errors.append(f"Insertion failed: {e}")

    # Upload log
    try:
        supabase.table("uploads").insert({
            "filename": filename,
            "upload_type": "Sem Result",
            "school": school,
            "branch": branch,
            "semester": semester,
            "academic_year": academic_year,
            "program": program
        }).execute()
    except Exception as e:
        errors.append(f"Upload log failed: {e}")

    # Final flash messages
    if inserted:
        flash(f"✅ {inserted} rows inserted successfully.")
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
        flash("Please upload a valid .xlsx file.")
        return redirect(url_for('admin_dashboard'))

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath)
        df.fillna('', inplace=True)
    except Exception as e:
        flash(f"Failed to read Excel file: {e}")
        return redirect(url_for('admin_dashboard'))

    # Normalize column names
    columns = [col.lower().strip().replace(" ", "_") for col in df.columns]
    df.columns = columns

    # Identify required columns
    reg_col = "reg_no" if "reg_no" in columns else "registration_number" if "registration_number" in columns else None
    if not reg_col or "subject_code" not in columns or "grade" not in columns:
        flash("Required columns missing: Reg_No/Registration Number, Subject_Code, Grade")
        return redirect(url_for('admin_dashboard'))

    updated = 0
    errors = []

    for _, row in df.iterrows():
        try:
            reg_no = str(row.get(reg_col, "")).strip()
            subject_code = str(row.get("subject_code", "")).strip()
            grade = str(row.get("grade", "")).strip()

            if not reg_no or not subject_code or not grade:
                continue

            # Check if record exists in database
            match_result = supabase.table("results").select("id").match({
                "reg_no": reg_no,
                "subject_code": subject_code
            }).execute()

            if match_result.data:
                record_id = match_result.data[0]['id']
                supabase.table("results").update({"grade": grade}).eq("id", record_id).execute()
                updated += 1
            # else: silently ignore if no match

        except Exception as e:
            errors.append(str(e))

    # Log the update attempt
    try:
        supabase.table("uploads").insert({
            "filename": filename,
            "upload_type": "EOD"
        }).execute()
    except Exception as e:
        errors.append(f"Upload log failed: {e}")

    if updated:
        flash(f"✅ {updated} rows updated successfully.")
    else:
        flash("⚠️ No matching records were found to update.")

    if errors:
        flash("❌ Some errors occurred: " + "; ".join(errors))

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

# ==========================

# Credit Tracker Logic and Routes

@app.route('/credit-tracker')
def credit_tracker_home():
    return render_template('credit_form.html')

@app.route('/view-credits')
def view_credits():
    reg_no = request.args.get('reg_no', '').strip()
    if not reg_no:
        return redirect(url_for('credit_tracker_home'))

    # Fetch all records of the student
    response = supabase.table("results").select("*").eq("reg_no", reg_no).execute()
    all_results = response.data

    if not all_results:
        return render_template("credit_view.html", student=None)

    # Prepare student profile
    student = {
        "name": all_results[0].get("name", "-"),
        "reg_no": reg_no,
        "program": all_results[0].get("program", "-"),
        "school": all_results[0].get("school", "-"),
        "branch": all_results[0].get("branch", "-"),
        "batch": all_results[0].get("batch", "-"),
        "semester": all_results[-1].get("semester", "-"),
        "cgpa": "-",  # Optional: Calculate if needed
    }

    semester_map = {}
    cleared_credits = 0
    backlog_credits = 0
    backlogs = []

    for record in all_results:
        sem = record.get("semester", "Unknown")
        grade = record.get("grade", "").strip().upper()
        credit_str = record.get("credits", "0").strip()

        # Safely parse credits (e.g., handle "3+1")
        try:
            credits = sum(float(x) for x in credit_str.split('+'))
        except:
            credits = 0.0

        if sem not in semester_map:
            semester_map[sem] = {
                "semester": sem,
                "subjects": [],
                "total_credits": 0,
                "cleared_credits": 0,
                "backlog_credits": 0
            }

        semester_map[sem]["subjects"].append(record)
        semester_map[sem]["total_credits"] += credits

        if grade in ["F", "S"]:
            semester_map[sem]["backlog_credits"] += credits
            backlog_credits += credits
            backlogs.append(record)
        else:
            semester_map[sem]["cleared_credits"] += credits
            cleared_credits += credits

    # Final metrics
    required_credits = 160
    completion_percentage = round((cleared_credits / required_credits) * 100, 2)

    return render_template(
        "credit_view.html",
        student=student,
        semester_data=list(semester_map.values()),
        credits_completed=cleared_credits,
        total_credits_required=required_credits,
        completion_percentage=completion_percentage,
        backlogs=backlogs,
        backlog_credits=backlog_credits
    )

# Basket Summary Logic and Route

@app.route('/view-basket-subjects')
def view_basket_subjects():
    reg_no = request.args.get('reg_no', '').strip()
    if not reg_no:
        return redirect(url_for('credit_tracker_home'))

    # Fetch student results
    results_resp = supabase.table("results").select("*").eq("reg_no", reg_no).execute()
    results = results_resp.data

    if not results:
        return render_template("basket_subjects.html", student=None)

    # Extract student info
    student = {
        "name": results[0].get("name", "-"),
        "reg_no": reg_no,
        "school": results[0].get("school", "-"),
        "branch": results[0].get("branch", "-"),
        "program": results[0].get("program", "-"),
        "batch": results[0].get("batch", "-")
    }

    # Use fallback defaults if fields missing
    program = student["program"] if student["program"] and student["program"] != "-" else "BTech"
    branch = student["branch"] if student["branch"] and student["branch"] != "-" else "All"

    # Basket requirement mapping
    BASKET_CREDIT_REQUIREMENTS = {
        "BTech": {
            "Basket I": 17,
            "Basket II": 12,
            "Basket III": 25,
            "Basket IV": 58,
            "Basket V": 48,
            "Total": 160
        },
        "BTech Honours": {
            "Basket I": 17,
            "Basket II": 12,
            "Basket III": 25,
            "Basket IV": 58,
            "Basket V": 68,
            "Total": 180
        },
        "BBA": {
            "Basket I": 10,
            "Basket II": 10,
            "Basket III": 20,
            "Basket IV": 60,
            "Basket V": 20,
            "Total": 120
        },
        "BSc Ag": {
            "Basket I": 18,
            "Basket II": 18,
            "Basket III": 20,
            "Basket IV": 96,
            "Basket V": 20,
            "Total": 172
        }
    }

    # Get credit requirement for the student's program
    basket_requirements = BASKET_CREDIT_REQUIREMENTS.get(program, {})

    # Fetch CBCS basket mappings (based on program & branch)
    cbcs_resp = supabase.table("cbcs_basket").select("*").or_(
        f"and(program.eq.{program},branch.eq.All),and(program.eq.{program},branch.eq.{branch})"
    ).execute()

    cbcs_map = cbcs_resp.data

    # subject_code → basket mapping
    subject_basket_map = {}
    for row in cbcs_map:
        subject_code = row.get("subject_code")
        if subject_code:
            subject_basket_map[subject_code] = {
                "basket": row.get("basket"),
                "credits": float(row.get("credits", 0)),
                "subject_name": row.get("subject_name", "")
            }

    # Group into baskets
    baskets = {}

    for row in results:
        sub_code = row['subject_code']
        grade = row.get('grade', '').strip().upper()

        if sub_code not in subject_basket_map:
            continue

        info = subject_basket_map[sub_code]
        basket = info['basket']
        credit = info['credits']
        sub_name = row.get("subject_name") or info['subject_name']

        if basket not in baskets:
            baskets[basket] = {
                "completed": [],
                "backlogs": [],
                "total_credits": basket_requirements.get(basket, 0),  # From mapping
                "cleared_credits": 0,
                "backlog_credits": 0
            }

        sub_data = {
            "subject_code": sub_code,
            "subject_name": sub_name,
            "credits": credit,
            "grade": grade,
            "semester": row.get("semester", "-")
        }

        if grade in ['F', 'S']:
            baskets[basket]["backlogs"].append(sub_data)
            baskets[basket]["backlog_credits"] += credit
        else:
            baskets[basket]["completed"].append(sub_data)
            baskets[basket]["cleared_credits"] += credit

    return render_template(
        "basket_subjects.html",
        student=student,
        basket_data=baskets,
        basket_requirements=basket_requirements
    )



if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, Response
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

    # ✅ Get distinct semester list and sort by semester number
    semesters_resp = supabase.table("results") \
        .select("semester") \
        .eq("reg_no", reg_no) \
        .execute()

    raw_semesters = list({row["semester"] for row in semesters_resp.data if row.get("semester")})

    # Extract semester number for sorting (e.g., "Sem 2" -> 2)
    def extract_sem_number(sem):
        try:
            return int(''.join(filter(str.isdigit, sem)))
        except:
            return float('inf')  # push unknowns to end

    semesters = sorted(raw_semesters, key=extract_sem_number)

    # ✅ Prepare chart data in sorted order
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

    # Rename columns
    df.columns = [col.strip().lower() for col in df.columns]
    column_map = {
        'registration no.': 'reg_no',
        'reg_no': 'reg_no',
        'subject code': 'subject_code',
        'grade': 'grade'
    }
    df.rename(columns={k: v for k, v in column_map.items() if k in df.columns}, inplace=True)

    if not {'reg_no', 'subject_code', 'grade'}.issubset(df.columns):
        flash("❌ Required columns missing: Registration No., Subject Code, Grade")
        return redirect(url_for('admin_dashboard'))

    # Build all (reg_no, subject_code) pairs from Excel
    keys = set()
    for _, row in df.iterrows():
        reg = str(row['reg_no']).strip()
        code = str(row['subject_code']).strip()
        if reg and code:
            keys.add((reg, code))

    if not keys:
        flash("❌ No valid records found.")
        return redirect(url_for('admin_dashboard'))

    # 🔍 Fetch all matching results in ONE query
    regnos = list({k[0] for k in keys})
    try:
        db_records = supabase.table("results").select("id, reg_no, subject_code") \
            .in_("reg_no", regnos).execute().data
    except Exception as e:
        flash(f"❌ Error fetching existing records: {e}")
        return redirect(url_for('admin_dashboard'))

    # 📌 Build lookup map
    id_map = {(r["reg_no"], r["subject_code"]): r["id"] for r in db_records}

    updated = 0
    errors = []

    for _, row in df.iterrows():
        reg_no = str(row.get("reg_no", "")).strip()
        subject_code = str(row.get("subject_code", "")).strip()
        grade = str(row.get("grade", "")).strip()

        key = (reg_no, subject_code)
        if key in id_map:
            try:
                supabase.table("results").update({
                    "grade": grade
                }).eq("id", id_map[key]).execute()
                updated += 1
            except Exception as e:
                errors.append(str(e))

    # ✅ Log the update
    try:
        supabase.table("uploads").insert({
            "filename": filename,
            "upload_type": "EOD"
        }).execute()
    except Exception as e:
        errors.append(f"Upload log failed: {e}")

    # ✅ Result messages
    if updated:
        flash(f"✅ {updated} grades updated successfully.")
    else:
        flash("⚠️ No matching records found to update.")

    if errors:
        flash("❌ Some errors occurred: " + "; ".join(errors))

    return redirect(url_for('admin_dashboard'))

@app.route('/get_semesters')
def get_semesters():
    reg_no = request.args.get('reg_no', '').strip()

    if not reg_no:
        return {'error': 'Registration number is required.', 'semesters': []}

    try:
        # Use `.select("semester").eq(...)` still due to Supabase limitation (no distinct in client lib)
        response = supabase.table("results") \
            .select("semester") \
            .eq("reg_no", reg_no) \
            .execute()

        # Collect and deduplicate semesters
        semesters = sorted(set(
            row["semester"] for row in response.data if row.get("semester")
        ))

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

    # ✅ Fetch all records of the student
    response = supabase.table("results").select("*").eq("reg_no", reg_no).execute()
    all_results = response.data

    if not all_results:
        return render_template("credit_view.html", student=None)

    # ✅ Extract student profile from the first result
    student = {
        "name": all_results[0].get("name", "-"),
        "reg_no": reg_no,
        "program": all_results[0].get("program", "-"),
        "school": all_results[0].get("school", "-"),
        "branch": all_results[0].get("branch", "-"),
        "batch": all_results[0].get("batch", "-"),
        "semester": all_results[-1].get("semester", "-"),
        "cgpa": "-",  # You can calculate if needed
    }

    # ✅ Define required credits based on program
    PROGRAM_CREDIT_REQUIREMENTS = {
        "BTech": 160,
        "Btech": 160,
        "BTech Honours": 180,
        "Btech Honours": 180,
        "BBA": 120,
        "Bba": 120,
        "BSc Ag": 172,
        "Bsc Ag": 172
    }

    program_key = student["program"].strip().title()
    required_credits = PROGRAM_CREDIT_REQUIREMENTS.get(program_key, 160)  # Default: 160

    # ✅ Initialize semester map and counters
    semester_map = {}
    cleared_credits = 0
    backlog_credits = 0
    backlogs = []

    for record in all_results:
        sem = record.get("semester", "Unknown")
        grade = record.get("grade", "").strip().upper()
        credit_str = record.get("credits", "0").strip()

        # ✅ Parse credits safely (e.g., handle "3+1")
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

    # ✅ Final metrics
    completion_percentage = round((cleared_credits / required_credits) * 100, 2) if required_credits else 0

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

    # ✅ Fetch student results
    results_resp = supabase.table("results").select("*").eq("reg_no", reg_no).execute()
    results = results_resp.data

    if not results:
        return render_template("basket_subjects.html", student=None)

    # ✅ Extract student info
    student = {
        "name": results[0].get("name", "-"),
        "reg_no": reg_no,
        "school": results[0].get("school", "-"),
        "branch": results[0].get("branch", "-"),
        "program": results[0].get("program", "-"),
        "batch": results[0].get("batch", "-")
    }

    # ✅ Normalize
    program = student["program"].strip().title() if student["program"] else "BTech"
    branch = student["branch"].strip().lower().replace(" ", "") if student["branch"] else "all"

    # ✅ Basket Credit Requirements
    BASKET_CREDIT_REQUIREMENTS = {
        "Btech": {
            "Basket I": 17, "Basket II": 12, "Basket III": 25,
            "Basket IV": 58, "Basket V": 48, "Total": 160
        },
        "Btech Honours": {
            "Basket I": 17, "Basket II": 12, "Basket III": 25,
            "Basket IV": 58, "Basket V": 68, "Total": 180
        },
        "Bba": {
            "Basket I": 60, "Basket II": 32, "Basket III": 12,
            "Basket IV": 12, "Basket V": 4, "Total": 120
        },
        "Bsc Ag": {
            "Basket I": 18, "Basket II": 18, "Basket III": 20,
            "Basket IV": 96, "Basket V": 20, "Total": 172
        }
    }

    basket_requirements = BASKET_CREDIT_REQUIREMENTS.get(program.title(), {})

    # ✅ Fetch CBCS data
    try:
        cbcs_resp = supabase.table("cbcs_basket").select("*").execute()
        cbcs_map = cbcs_resp.data
    except Exception as e:
        flash(f"❌ Error fetching CBCS mappings: {e}", "danger")
        return render_template("basket_subjects.html", student=student, basket_data={}, basket_requirements={})

    # ✅ Build subject_code → basket map with filtering
    subject_basket_map = {}
    for row in cbcs_map:
        sub_code = row.get("subject_code", "").strip()
        cbcs_prog = row.get("program", "").strip().title()
        cbcs_branch = row.get("branch", "").strip().lower().replace(" ", "")

        # Match combinations
        match = (
            (cbcs_prog == program and cbcs_branch == branch) or
            (cbcs_prog == program and cbcs_branch == "all") or
            (cbcs_prog == "All" and cbcs_branch == "all") or
            (cbcs_prog == "All" and cbcs_branch == branch)
        )

        if sub_code and match:
            try:
                credits = float(row.get("credits", 0))
            except:
                credits = 0
            subject_basket_map[sub_code] = {
                "basket": row.get("basket", "Unknown"),
                "credits": credits,
                "subject_name": row.get("subject_name", "")
            }

    # ✅ Group into baskets
    baskets = {}
    unmatched = 0

    for row in results:
        sub_code = row.get("subject_code", "").strip()
        grade = row.get("grade", "").strip().upper()

        if sub_code not in subject_basket_map:
            unmatched += 1
            continue

        info = subject_basket_map[sub_code]
        basket = info["basket"]
        credit = info["credits"]
        sub_name = row.get("subject_name") or info["subject_name"]

        if basket not in baskets:
            baskets[basket] = {
                "completed": [],
                "backlogs": [],
                "total_credits": basket_requirements.get(basket, 0),
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

        if grade in ["F", "S"]:
            baskets[basket]["backlogs"].append(sub_data)
            baskets[basket]["backlog_credits"] += credit
        else:
            baskets[basket]["completed"].append(sub_data)
            baskets[basket]["cleared_credits"] += credit

    if unmatched > 0:
        flash(f"{unmatched} subject(s) did not match any CBCS basket mapping and were ignored.", "info")

    # ✅ Sort baskets like I, II, III, IV...
    def basket_order_key(basket_name):
        try:
            return int(basket_name.split()[-1])
        except:
            return 999  # Unknown baskets at end

    sorted_baskets = dict(sorted(baskets.items(), key=lambda x: basket_order_key(x[0])))

    return render_template(
        "basket_subjects.html",
        student=student,
        basket_data=sorted_baskets,
        basket_requirements=basket_requirements
    )

from collections import defaultdict
from flask import request, render_template, flash

@app.route('/basket-summary-report', methods=['GET', 'POST'])
def basket_summary_report():
    try:
        # 📌 Dropdown values from results table
        dropdown_data = supabase.table("results").select("school", "branch", "program").execute().data
        unique_schools = sorted({d.get("school") for d in dropdown_data if d.get("school")})
        unique_programs = sorted({d.get("program") for d in dropdown_data if d.get("program")})
        unique_branches = sorted({d.get("branch") for d in dropdown_data if d.get("branch")})

    except Exception as e:
        flash(f"❌ Error fetching dropdowns: {e}", "danger")
        return render_template("basket_summary_report.html", data=[], baskets=[], schools=[], programs=[], branches=[])

    if request.method == 'POST':
        school = request.form.get('school')
        program = request.form.get('program')
        branch = request.form.get('branch')
        start_reg = request.form.get('start_reg')
        end_reg = request.form.get('end_reg')

        try:
            # ✅ Get student results in range
            student_resp = supabase.table("results") \
                .select("*") \
                .gte("reg_no", start_reg) \
                .lte("reg_no", end_reg) \
                .eq("school", school) \
                .eq("branch", branch) \
                .eq("program", program) \
                .execute()

            student_results = student_resp.data
            if not student_results:
                flash("⚠️ No student records found.", "warning")
                return render_template("basket_summary_report.html", data=[], baskets=[], schools=unique_schools, programs=unique_programs, branches=unique_branches)

            # ✅ CBCS Data
            cbcs_map = supabase.table("cbcs_basket").select("*").execute().data

            # 🔁 Build subject_code → list of basket options
            subject_basket_map = defaultdict(list)
            for row in cbcs_map:
                sub_code = row.get("subject_code", "").strip()
                prog = row.get("program", "").strip().lower()
                brnch = row.get("branch", "").strip().lower().replace(" ", "")
                basket = row.get("basket", "").strip()
                credits = float(row.get("credits", 0))

                if sub_code and basket:
                    subject_basket_map[sub_code].append({
                        "program": prog,
                        "branch": brnch,
                        "basket": basket,
                        "credits": credits
                    })

            # ✅ Basket Requirement Map
            BASKET_CREDIT_REQUIREMENTS = {
                "Btech": {
                    "Basket I": 17, "Basket II": 12, "Basket III": 25,
                    "Basket IV": 58, "Basket V": 48, "Total": 160
                },
                "Btech Honours": {
                    "Basket I": 17, "Basket II": 12, "Basket III": 25,
                    "Basket IV": 58, "Basket V": 68, "Total": 180
                },
                "Bba": {
                    "Basket I": 60, "Basket II": 32, "Basket III": 12,
                    "Basket IV": 12, "Basket V": 4, "Total": 120
                },
                "Bsc Ag": {
                    "Basket I": 18, "Basket II": 18, "Basket III": 20,
                    "Basket IV": 96, "Basket V": 20, "Total": 172
                }
            }
            basket_labels = list(BASKET_CREDIT_REQUIREMENTS.get(program.title(), {}).keys())[:-1]  # Exclude 'Total'

            # ✅ Aggregation per student
            student_data = defaultdict(lambda: {
                "name": "",
                "reg_no": "",
                "branch": "",
                "baskets": defaultdict(float),
                "backlog_credits": 0.0,
                "total": 0.0
            })

            for row in student_results:
                reg_no = row.get("reg_no", "").strip()
                name = row.get("name", "-")
                br = row.get("branch", "-")

                subject_code = row.get("subject_code", "").strip()
                grade = row.get("grade", "").strip().upper()

                student = student_data[reg_no]
                student["name"] = name
                student["reg_no"] = reg_no
                student["branch"] = br

                if subject_code not in subject_basket_map:
                    continue

                matched = None
                for option in subject_basket_map[subject_code]:
                    prog = option["program"]
                    brnch = option["branch"]
                    if (prog == program.lower() or prog == "all") and (brnch == branch.lower().replace(" ", "") or brnch == "all"):
                        matched = option
                        break

                if not matched:
                    continue

                credits = matched["credits"]
                basket = matched["basket"]

                if grade in ["F", "S"]:
                    student["backlog_credits"] += credits
                else:
                    student["baskets"][basket] += credits
                    student["total"] += credits

            final_data = sorted(student_data.values(), key=lambda x: x["reg_no"])

            return render_template("basket_summary_report.html",
                                   data=final_data,
                                   baskets=basket_labels,
                                   schools=unique_schools,
                                   programs=unique_programs,
                                   branches=unique_branches)

        except Exception as e:
            flash(f"❌ Error processing report: {str(e)}", "danger")
            return render_template("basket_summary_report.html", data=[], baskets=[], schools=unique_schools, programs=unique_programs, branches=unique_branches)

    # GET method
    return render_template("basket_summary_report.html",
                           data=[],
                           baskets=[],
                           schools=unique_schools,
                           programs=unique_programs,
                           branches=unique_branches)

#==========================
#=== Logic for Sitemap ===
#==========================
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    base_url = "https://my-result.onrender.com"  # ✅ Your actual live domain
    static_routes = []

    # Collect all static GET routes with no dynamic params
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0 and not rule.rule.startswith("/static"):
            url = f"{base_url}{rule.rule}"
            static_routes.append(url)

    # Build XML structure
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in static_routes:
        xml.append("  <url>")
        xml.append(f"    <loc>{url}</loc>")
        xml.append(f"    <lastmod>{datetime.utcnow().date()}</lastmod>")
        xml.append("    <changefreq>weekly</changefreq>")
        xml.append("    <priority>0.8</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")
    sitemap_xml = "\n".join(xml)

    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/google53dcc92479ba04f1.html')
def google_verify():
    return 'google-site-verification: google53dcc92479ba04f1.html'

if __name__ == '__main__':
    app.run(debug=True)

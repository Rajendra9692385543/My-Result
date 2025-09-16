
# 🎓 MyResult – Student Result & Credit Tracker Portal (v4)

A full-fledged academic portal to **view student results**, **track credits**, and **manage uploads** via a secure admin panel.  
Version **v4** introduces advanced **credit tracker reports, CBCS basket analysis, result uploads with school/program mapping, and PDF/Excel exports.**

---

## 🚀 Features

### 🔍 Student Result Viewer
- Search by **Registration Number**.
- Displays **subject-wise marks, grades, SGPA, CGPA**.
- Visual **SGPA/CGPA charts** across semesters.
- **Download Reports**:
  - PDF (Semester-wise styled result card).
  - Excel (Credit + Backlog summary).

### 📊 Credit Tracker
- Track **total, cleared, pending, and backlog credits** semester-wise.
- Visualizations:
  - Pie chart (cleared vs backlog).
  - Progress bar for overall completion.
- Lists **backlog subjects with credit details**.
- **Basket Summary Report** (CBCS):
  - Generate basket-wise credit completion for reg_no ranges.
  - Semester & year-wise breakdown.
  - Export to **Excel** or **PDF**.

### 🔐 Admin Panel
- **Secure login** (Superadmin & Admin roles).
- **Result Uploads**:
  - Regular results: Insert/Update with School, Branch, Program, Semester, Batch.
  - Re-exam results: Update only (no new rows, existing school/branch untouched).
- **CBCS Basket Uploads**:
  - Upload basket-subject mapping via Excel.
  - Supports School/Branch/Program/Year/Semester filters.
- **Admin Management** (for Superadmin):
  - Add new admins.
  - Delete existing admins.
- **Upload Logs**:
  - Filename, details, timestamp.
  - Status highlighted (🟩 New / 🟨 Updated).
  - Download links for uploaded files.

### 🌐 SEO & Static Pages
- **Sitemap (`/sitemap.xml`)**: Auto-generates static + student result URLs.
- **robots.txt**: Blocks sensitive routes, allows indexing of safe routes, includes sitemap link.
- **Google site verification** endpoint.
- Static **About Page**.

---

## 🛠️ Tech Stack

| Layer       | Technology             |
|-------------|------------------------|
| Frontend    | HTML, Bootstrap 5      |
| Backend     | Flask (Python)         |
| Database    | SQLite (via SQLAlchemy)|
| Data Tools  | Pandas, OpenPyXL, ReportLab |
| Charts      | Chart.js               |
| Auth        | Role-based (Admin, Superadmin) |

---

## 📤 Excel Upload Format (Admin)

| Column Name   | Description                        |
|---------------|------------------------------------|
| Reg_No        | Student registration number        |
| Name          | Student name                       |
| Subject_Code  | Subject code                       |
| Subject_Name  | Subject name                       |
| Type          | Theory / Lab / Project             |
| Credits       | Example: `3` or `3.0+1.0`          |
| Grade         | Example: A, B, C, F, etc.          |

🔹 **Regular Results** → Adds School, Branch, Program, Semester, Batch automatically.  
🔹 **Re-exam Results** → Updates only by `reg_no` + `subject_code`.

---

## 🆕 v4 Updates

- ✅ Added **School, Branch, Program, Semester, Batch** in upload form.  
- ✅ Support for **Re-exam results** (update-only mode).  
- ✅ New **Basket Summary Report** with PDF/Excel exports.  
- ✅ **Admin Dashboard** shows result files table with status (new/update).  
- ✅ Superadmin can **add/delete admins**.  
- ✅ Downloadable **PDF & Excel reports** for students and basket analysis.  
- ✅ SEO enhancements: **sitemap.xml**, **robots.txt**, **about page**.  
- ✅ Improved credit tracker with backlog subject details.

---

## 📥 Installation

1. Clone the repo:
```bash
   git clone https://github.com/Rajendra9692385543/My-Result.git
   cd My-Result
````

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask app:

   ```bash
   flask run
   ```

5. Visit:

   ```
   http://127.0.0.1:5000/
   ```

---

## 📈 Credit Calculation Logic

* **Total Credits** = sum of all subjects’ credits.
* **Cleared Credits** = subjects with grades not in `[F, S]`.
* **Backlogs** = subjects with grades in `[F, S]`.
* **Pending Credits** = required - (cleared + backlog).
* Charts show semester & overall credit status.

---

## 📌 Roadmap

* [ ] Student login portal with personalized dashboards.
* [ ] Export results as PDF (auto for each student).
* [ ] Email/SMS notifications for result updates.
* [ ] Migrate to **Supabase/PostgreSQL** for production scale.
* [ ] Mobile-friendly progressive web app (PWA).

---

## 📷 Screenshots (To be added)

* Student Result Page (SGPA/CGPA Chart).
* Credit Tracker with Pie Chart & Progress Bar.
* Admin Dashboard with Upload Logs.
* Basket Summary Report (Excel/PDF).

---

## 🧑‍💻 Created By

**Rajendra Das**
💌 [rajendradas5543@gmail.com](mailto:rajendradas5543@gmail.com)
🌐 GitHub: [Rajendra9692385543](https://github.com/Rajendra9692385543)


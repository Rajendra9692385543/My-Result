# 🎓 MyResult – Student Result & Credit Tracker Portal
An academic portal to view student results, track credit progress, and manage uploads via admin panel.

# 🚀 Features
🔍 Student Result Viewer
Enter registration number and semester to view detailed results.

Displays subject-wise marks, grades, SGPA, CGPA, academic year.

Includes visual CGPA chart across all semesters.

# 📊 Credit Tracker (New Module)
Track total, cleared, and remaining credits semester-wise.

Each semester has:

Subject-wise details

Pie chart visualization (cleared vs backlog)

Summary view with:

Total credits required vs completed

Progress bar

Pie chart showing completed, pending, and backlog credits

Displays backlog subjects with credit count.

# 🔐 Admin Panel
Login-protected admin dashboard

Upload results (bulk insert/update) via Excel files

Metadata logging (school, branch, semester, academic year)

View upload history and status

# 🛠️ Tech Stack
Layer	Tech
Frontend	HTML, Bootstrap 5
Backend	Flask (Python)
Database	Supabase (PostgreSQL)
Charts	Chart.js
File Upload	Excel (.xlsx via Pandas)

# 📤 Excel Upload Format (for admin)
Column Name	Description
Reg_No	Student registration no.
Name	Student name
Subject_Code	Code of the subject
Subject_Name	Name of the subject
Type	Theory/Lab/Project
Credits	e.g. 3 or 3.0+1.0
Grade	A, B, C, F, etc.

# 🧪 Admin Login
Will Setup this will the help of Supabase OTP auth 

# 📈 Credit Calculation Logic
Total credits = sum of all course credits

Cleared: if grade not in ['F', 'S']

Backlogs: grade is F or S

Pending: difference between required and (cleared + backlog)

Pie charts display semester and overall credit status

# 💡 Future Enhancements
Export results as PDF

Add re-exam tracking

Student login panel

Dynamic credit requirements based on branch/program

# 🧑‍💻 Created By
Rajendra
💌 rajendradas5543@gmail.com
🌐 GitHub: Rajendra9692385543

# test
The system allows you to upload student learning results, analyze performance by group, subject, and instructor, visualize key performance indicators (KPIs), and generate professional reports in CSV and PDF formats. It supports a role-based access model, REST API, and user action logging.

# 🎓 Academic Performance Analytics (Django)

> From basic dashboards to advanced PDF reports: analyze how students learn, track KPIs, and automate reporting for an electronic university. 💪🚀

> [!NOTE]
> This project was originally created as a university graduation thesis.  
> It is not a full-scale production system, but a compact, educational analytics platform built with Django.

---

<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen" />
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" />
  <img src="https://img.shields.io/badge/django-5.2.8-green" />
  <img src="https://img.shields.io/badge/report-PDF-red" />
  <img src="https://img.shields.io/badge/license-MIT-yellow" />
</p>

---

From CSV import to PDF export, this project shows how to build an **end-to-end academic analytics system**:

- Upload raw student results  
- Aggregate and visualize data per group, discipline, teacher, and semester  
- Export data and analytics to **CSV** and **PDF**  
- Restrict access with **role-based permissions**  
- Expose metrics through a small **REST API**

Have fun exploring the code! 

---

## 1️⃣ What is this project?

<details>
<summary><strong>Click to expand</strong></summary>

This repository contains a **Django-based web application** that automates:

- importing student learning results from CSV;
- calculating average grades and other metrics;
- visualizing performance via dashboards and charts;
- exporting reports to CSV and PDF;
- logging critical actions (uploads, exports, etc.);
- separating access for teachers, managers, and admins.

It was built as a **graduation thesis** on the topic of:

> “Automation of analysis and evaluation of educational process indicators in an electronic university”.

</details>

---

## 2️⃣ What can the system do?

<details>
<summary><strong>Core features</strong></summary>

### 📥 Data Import
- CSV upload (`;` separator, UTF-8)
- Auto-creation of:
  - groups  
  - students  
  - disciplines  
  - teachers  
  - semesters  
  - results (grade + attendance)

### 📊 Analytics Dashboard
- Average grade per **group** and **discipline**
- Yearly average grade chart
- KPI cards:
  - total students
  - total groups
  - total disciplines
  - global average grade
- Filters: by **semester**, **discipline**, **teacher**

### 👨‍🏫 Teacher Mode
- Teacher sees only **their own** disciplines and groups
- Teacher cannot upload or export data

### 📈 Detail Pages
- **Group profile**:
  - average grade per discipline
  - average grade per student
- **Discipline profile**:
  - group performance
  - student ranking

### 📤 Export
- Export filtered results to **CSV**
- Generate aggregated **PDF** report (Cyrillic-friendly font)

### 🔐 Roles
- **Teacher** — read-only analytics for their courses
- **Manager** — upload CSV, export CSV/PDF, full analytics
- **Admin** — full control + Django admin

### 🧾 Audit Log
- Logs:
  - imports
  - CSV exports
  - PDF exports

### 🌓 Dark Mode
- Light/dark theme toggle
- Preference stored in `localStorage`

### 🧩 REST API
- `/api/summary/` — JSON with:
  - KPI
  - group stats
  - yearly stats

</details>

---

## 3️⃣ How is the project structured?

<details>
<summary><strong>Project layout</strong></summary>

```text
.
├─ config/              # Django project settings & URLs
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ asgi.py
├─ analytics/           # Main application
│  ├─ models.py         # Group, Student, Discipline, Teacher, Result, Semester, AuditLog
│  ├─ views.py          # Dashboard, profiles, upload, export, API
│  ├─ urls.py           # App routes
│  ├─ admin.py          # Admin registration
│  ├─ forms.py          # CSV upload form
│  ├─ templates/
│  │   └─ analytics/    # HTML templates (dashboard, profiles, upload, etc.)
│  ├─ static/
│  │   └─ analytics/style.css   # Light/Dark theme
│  └─ fonts/
│      └─ DejaVuSans.ttf        # Font for Cyrillic PDF
├─ docs/                # Extra docs (architecture, API, diagrams, report)
├─ manage.py
├─ requirements.txt
├─ README.md

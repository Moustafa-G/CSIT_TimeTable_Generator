# 🎓 CSIT Timetable Generator

Automated timetable generation system for **Computer Science and Information Technology (CSIT)** departments.  
It uses **Python + OR-Tools (CSP Solver)** to schedule lectures, labs, and tutorials efficiently — respecting all constraints like instructors, rooms, and available time slots.

---

## 🚀 Features
✅ Generates optimized timetables automatically  
✅ Supports multiple years & departments (CSC, AID, CNC, BIF)  
✅ Handles instructors, TAs, rooms, and timeslot constraints  
✅ Exports results directly to **Excel (.xlsx)**  
✅ Modular design — easy to extend or customize  

---

## 🗂️ Project Structure
```
CSIT_TimeTable_Generator/
│
├── data/                 # Input data files
│   ├── Courses.xlsx
│   ├── Sections.xlsx
│   ├── Instructor.xlsx
│   ├── TAs.xlsx
│   ├── Halls.xlsx
│   └── TimeSlots.xlsx
│
├── output/               # Generated timetables (Excel)
│
├── timetable_generator.py # Main driver script
├── requirements.txt       # Python dependencies
├── readme.md
└── .gitignore
```

---

## ⚙️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Moustafa-G/CSIT_TimeTable_Generator.git
cd CSIT_TimeTable_Generator
```

### 2️⃣ Create a virtual environment (recommended)
```bash
python -m venv .venv
.venv\Scripts\activate    # (Windows)
# or source .venv/bin/activate (Linux/Mac)
```

### 3️⃣ Install requirements
```bash
pip install -r requirements.txt
```

---

## 🧠 Usage
Simply run the generator:
```bash
python timetable_generator.py
```

Your timetables will be automatically generated in the `output/` folder as Excel files:
```
output/
├── timetable_year1.xlsx
├── timetable_year2.xlsx
├── timetable_year3_CSC.xlsx
├── timetable_year4_BIF.xlsx
└── ...
```

---

## 🧩 Technologies Used
- 🐍 **Python 3.12+**
- 🧮 **Google OR-Tools** (for constraint satisfaction)
- 📊 **Pandas** (data processing)
- 💾 **OpenPyXL** (Excel export)

---

## 🧑‍💻 Developers
👤 **Moustafa A. G. Abdelhamid**  
👤 **Ahmed Abdalla El Tahan**

---

⭐ If you like this project, please consider **starring** the repo on GitHub — it helps a lot! 🌟

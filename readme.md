# 🧮 CSIT Timetable Generator

This project automatically generates a **conflict-free timetable** for CSIT courses using **Constraint Satisfaction Problem (CSP)** techniques powered by **Google OR-Tools**.

---

## 🚀 Features
- Generates valid timetables for all sections and halls.
- Ensures every section is assigned exactly one slot and one room.
- Uses **OR-Tools CP-SAT Solver** for optimal scheduling.
- Fully Excel-based — easy to update and extend.
- Supports adding instructor preferences, hall capacities, and TA assignments.

---

## 🧩 Folder Structure
CSIT_TimeTable_Generator/
│
├── timetable_generator.py # Main script
├── requirements.txt # Dependencies
├── data/ # Input Excel files
└── output/ # Generated timetables

yaml
Copy code

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/CSIT_TimeTable_Generator.git
cd CSIT_TimeTable_Generator

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
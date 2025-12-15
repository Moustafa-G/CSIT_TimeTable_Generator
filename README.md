# Timetable Scheduler - Python Port

A complete Python CSP (Constraint Satisfaction Problem) solver for university timetable generation.

## Project Structure

```
timetable_scheduler/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                  # This file
├── data/
│   └── database.db           # SQLite database (your existing DB)
├── models/
│   ├── __init__.py
│   └── data_models.py        # Data classes (Course, Instructor, etc.)
├── database/
│   ├── __init__.py
│   └── database_manager.py   # Database access layer
├── solver/
│   ├── __init__.py
│   └── csp_solver.py         # CSP solver implementation
└── gui/
    ├── __init__.py
    └── main_window.py        # PyQt6 main window
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Create a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Place your database**:
   - Copy your `database.db` file to the `data/` directory
   - Or use the file dialog in the application to select any location

## Running the Application

### GUI Mode
```bash
python main.py
```

This opens the PyQt6 graphical interface where you can:
1. Load a database file
2. Solve the timetable scheduling problem
3. View the results
4. Export to JSON

### Command Line Mode (Optional)

You can also create a command-line script if needed:

```python
# cli.py
from database.database_manager import DatabaseManager
from solver.csp_solver import CSPSolver
import json

def main():
    # Load data
    db = DatabaseManager("data/database.db")
    courses = [c for c in db.get_courses() if 1 <= c.year <= 4]
    instructors = db.get_instructors()
    instructor_courses = db.get_instructor_courses()
    rooms = db.get_rooms()
    time_slots = db.get_time_slots()
    
    # Create solver
    solver = CSPSolver(courses, instructors, instructor_courses, rooms, time_slots)
    solver.build_lecture_variables()
    solver.build_domains()
    
    # Solve
    result = solver.solve()
    
    # Print result
    solver.print_result(result)
    
    # Export JSON (optional)
    if result.success:
        # ... generate JSON ...
        pass

if __name__ == "__main__":
    main()
```

## Features

### Core Functionality
- ✅ Complete CSP solver with backtracking
- ✅ Minimum Remaining Values (MRV) heuristic
- ✅ Forward checking for domain reduction
- ✅ Hard constraint enforcement
- ✅ Soft constraint cost calculation
- ✅ Multi-threaded solving (doesn't freeze GUI)

### Constraints Handled
- **Hard Constraints**:
  - No instructor conflicts
  - No room conflicts
  - No group conflicts (same year/group/time)
  - No specialization conflicts
  - Course consistency (same professor for all lecture groups)

- **Soft Constraints**:
  - Minimize early morning classes
  - Minimize multiple sessions per day for same course

### GUI Features
- Load database from file dialog
- Real-time progress updates
- View complete solution
- Export to JSON format
- Monospace output for readability

## Performance Notes

The Python version maintains the same algorithmic complexity as the C++ version:
- Uses the same backtracking search with MRV
- Implements identical forward checking
- Has the same constraint checking logic

However, Python will be slower than C++ for the following reasons:
- Interpreted vs compiled
- Dynamic typing overhead
- GIL (Global Interpreter Lock) limitations

**Expected performance**: 2-5x slower than C++ depending on problem size.

## Troubleshooting

### Import Errors
If you get import errors, make sure:
1. You're in the project root directory
2. Your virtual environment is activated
3. All `__init__.py` files are present

### Database Not Found
Make sure the database file path is correct. You can either:
- Place `database.db` in the `data/` folder
- Use the "Load Database" button to select it

### Solver Takes Too Long
The CSP solver can take several seconds to several minutes depending on:
- Number of courses
- Number of constraints
- Available time slots and rooms

The GUI will show progress and remain responsive.

## Development

### Adding New Features

**New Constraint**:
```python
# In csp_solver.py, modify is_hard_conflict()
def is_hard_conflict(self, a, b, va, vb):
    # ... existing checks ...
    
    # Add your new constraint
    if your_new_constraint_violated(a, b, va, vb):
        return True
    
    return False
```

**New Heuristic**:
```python
# In csp_solver.py, modify the MRV selection in dfs()
chosen = select_variable_with_your_heuristic(...)
```

## Testing

Create a test file to verify functionality:

```python
# test_solver.py
from database.database_manager import DatabaseManager
from solver.csp_solver import CSPSolver

def test_basic_solve():
    db = DatabaseManager("data/database.db")
    courses = db.get_courses()[:5]  # Test with 5 courses
    # ... rest of setup ...
    
    solver = CSPSolver(courses, instructors, ic, rooms, ts)
    solver.build_lecture_variables()
    solver.build_domains()
    result = solver.solve()
    
    assert result.success
    print(f"✓ Test passed! Solved in {result.solve_seconds:.2f}s")

if __name__ == "__main__":
    test_basic_solve()
```

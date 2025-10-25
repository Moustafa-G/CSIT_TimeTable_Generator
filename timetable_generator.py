

import pandas as pd
from ortools.sat.python import cp_model
from collections import defaultdict
import time
import math

class CSITTimetableGenerator:
    """Production-ready CSIT Timetable Generator with graduation project support."""
    
    # Graduation project course codes
    GRADUATION_PROJECTS = ['CSC413', 'AID414', 'CNC414', 'BIF410']
    
    def __init__(self, target_year=None, target_specialization=None):
        self.target_year = target_year
        self.target_specialization = target_specialization
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Solver configuration
        self.solver.parameters.num_search_workers = 8
        self.solver.parameters.max_time_in_seconds = 1800
        self.solver.parameters.log_search_progress = False
        
        # Data structures
        self.courses = {}
        self.sections = []
        self.groups = {}
        self.instructors = {}
        self.tas = {}
        self.halls = {}
        self.timeslots = []
        
        self.session_vars = defaultdict(list)
        
        # For tracking shared course assignments across specializations
        self.shared_course_assignments = {}
    
    def load_data(self):
        """Load all academic data from Excel files."""
        spec_label = f" {self.target_specialization}" if self.target_specialization else ""
        print(f"Loading data for Year {self.target_year}{spec_label}...")
        
        # Load courses
        courses_df = pd.read_excel("data/Courses.xlsx")
        for _, row in courses_df.iterrows():
            if self.target_year and row['Year'] != self.target_year:
                continue
            
            # For Years 3-4, filter by specialization
            if self.target_year in [3, 4] and self.target_specialization:
                spec = row['Specialization'] if pd.notna(row['Specialization']) else None
                if spec != self.target_specialization:
                    continue
            
            course_code = row['CourseCode']
            if pd.isna(course_code):
                continue
                
            lec_raw = row['LecSlots'] if pd.notna(row['LecSlots']) else 0
            tut_raw = row['TutSlots'] if pd.notna(row['TutSlots']) else 0
            lab_raw = row['LabSlots'] if pd.notna(row['LabSlots']) else 0
            
            # Check if this is a graduation project
            is_grad_project = (course_code in self.GRADUATION_PROJECTS and lec_raw == 4)
            
            self.courses[course_code] = {
                'year': row['Year'],
                'specialization': row['Specialization'] if pd.notna(row['Specialization']) else 'General',
                'title': row['Title'],
                'lec_count': math.ceil(lec_raw),
                'lec_duration': lec_raw,
                'tut_count': math.ceil(tut_raw),
                'tut_duration': tut_raw,
                'lab_count': math.ceil(lab_raw),
                'lab_duration': lab_raw,
                'is_graduation_project': is_grad_project
            }
        
        # Load sections
        sections_df = pd.read_excel("data/Sections.xlsx")
        for _, row in sections_df.iterrows():
            if self.target_year and row['Year'] != self.target_year:
                continue
            
            if self.target_year in [3, 4] and self.target_specialization:
                dept = row['DepartmentName'] if pd.notna(row['DepartmentName']) else 'General'
                if dept != self.target_specialization:
                    continue
            
            section_data = {
                'faculty': row['FacultyName'],
                'year': row['Year'],
                'department': row['DepartmentName'] if pd.notna(row['DepartmentName']) else 'General',
                'group': row['GroupNumber'],
                'section': row['SectionNumber'],
                'students': row['StudentNumber']
            }
            self.sections.append(section_data)
            
            group_key = (
                row['Year'],
                row['DepartmentName'] if pd.notna(row['DepartmentName']) else 'General',
                row['GroupNumber']
            )
            
            if group_key not in self.groups:
                self.groups[group_key] = {
                    'year': row['Year'],
                    'department': row['DepartmentName'] if pd.notna(row['DepartmentName']) else 'General',
                    'group_number': row['GroupNumber'],
                    'sections': [],
                    'total_students': 0
                }
            
            self.groups[group_key]['sections'].append(section_data)
            self.groups[group_key]['total_students'] += row['StudentNumber']
        
        # Load instructors
        instructors_df = pd.read_excel("data/Instructor.xlsx")
        for _, row in instructors_df.iterrows():
            qualified = str(row['QualifiedCourses']).split(',') if pd.notna(row['QualifiedCourses']) else []
            self.instructors[row['InstructorID']] = {
                'name': row['Name'],
                'qualified': [c.strip() for c in qualified]
            }
        
        # Load TAs
        tas_df = pd.read_excel("data/TAs.xlsx")
        for _, row in tas_df.iterrows():
            qualified = str(row['QualifiedCourses (with Role)']).split(',') if pd.notna(row['QualifiedCourses (with Role)']) else []
            self.tas[row['TA_ID']] = {
                'name': row['Name'],
                'qualified': [c.strip() for c in qualified]
            }
        
        # Load halls
        halls_df = pd.read_excel("data/Halls.xlsx")
        capacity_col = None
        for col in halls_df.columns:
            if 'capacity' in col.lower():
                capacity_col = col
                break
        
        if not capacity_col:
            raise ValueError("Could not find capacity column in Halls.xlsx")
        
        for _, row in halls_df.iterrows():
            hall_id = f"{row['Building']}_{row['Space']}"
            hall_space = str(row['Space']).upper()
            
            self.halls[hall_id] = {
                'building': row['Building'],
                'space': row['Space'],
                'capacity': int(row[capacity_col]) if pd.notna(row[capacity_col]) else 25,
                'type': row['Type of Space'],
                'is_phy_lab': 'PHY' in hall_space and 'LAB' in hall_space
            }
        
        # Load timeslots
        timeslots_df = pd.read_excel("data/TimeSlots.xlsx")
        for _, row in timeslots_df.iterrows():
            self.timeslots.append({
                'id': row['TimeSlotID'],
                'day': row['Day'],
                'start': row['StartTime'],
                'end': row['EndTime']
            })
        
        print(f"Loaded: {len(self.courses)} courses, {len(self.sections)} sections, "
              f"{len(self.groups)} groups, {len(self.instructors)} instructors, "
              f"{len(self.tas)} TAs, {len(self.halls)} halls, {len(self.timeslots)} timeslots")
    
    def get_groups_for_course(self, course_code):
        """Get all groups that need a specific course."""
        course = self.courses[course_code]
        matching_groups = []
        
        for group_key, group_info in self.groups.items():
            if group_info['year'] == course['year']:
                if course['specialization'] == 'General' or group_info['department'] == course['specialization']:
                    matching_groups.append(group_info)
        
        return matching_groups
    
    def get_sections_for_course(self, course_code):
        """Get all sections that need a specific course."""
        course = self.courses[course_code]
        matching_sections = []
        
        for section in self.sections:
            if section['year'] == course['year']:
                if course['specialization'] == 'General' or section['department'] == course['specialization']:
                    matching_sections.append(section)
        
        return matching_sections
    
    def get_instructors_for_course(self, course_code):
        """Get instructors qualified to teach a course."""
        qualified = []
        for instructor_id, info in self.instructors.items():
            if course_code in info['qualified']:
                qualified.append(instructor_id)
        return qualified
    
    def get_tas_for_course(self, course_code, role='LAB'):
        """Get TAs qualified for a course and role."""
        qualified = []
        for ta_id, info in self.tas.items():
            for q in info['qualified']:
                if course_code in q and role in q:
                    qualified.append(ta_id)
                    break
        return qualified
    
    def get_suitable_halls(self, session_type, student_count, course_code=None):
        """Get halls suitable for a session type and capacity."""
        suitable = []
        is_phy_lab = (course_code == 'PHY113' and session_type == 'LAB')
        
        for hall_id, info in self.halls.items():
            if is_phy_lab:
                if not info.get('is_phy_lab', False):
                    continue
            else:
                if info.get('is_phy_lab', False):
                    continue
            
            if session_type == 'LAB' and info['type'] != 'Lab':
                continue
            if session_type in ['LEC', 'TUT'] and info['type'] == 'Lab':
                continue
            
            if info['capacity'] >= student_count * 0.8:
                suitable.append(hall_id)
        
        return suitable
    
    def is_consecutive_slot(self, slot1_id, slot2_id):
        """Check if two slots are consecutive."""
        if slot1_id >= len(self.timeslots) or slot2_id >= len(self.timeslots):
            return False
        
        slot1 = self.timeslots[slot1_id]
        slot2 = self.timeslots[slot2_id]
        
        return (slot1['day'] == slot2['day'] and slot1['end'] == slot2['start'])
    
    def get_full_day_slots(self):
        """Get all possible 8-consecutive-slot blocks (full days) for graduation projects."""
        full_days = []
        
        # Group slots by day
        slots_by_day = defaultdict(list)
        for i, slot in enumerate(self.timeslots):
            slots_by_day[slot['day']].append(i)
        
        # For each day, check if we have 8 consecutive slots
        for day, slot_ids in slots_by_day.items():
            if len(slot_ids) >= 8:
                # Check if first 8 slots are consecutive
                is_consecutive = True
                for i in range(7):
                    if not self.is_consecutive_slot(slot_ids[i], slot_ids[i+1]):
                        is_consecutive = False
                        break
                
                if is_consecutive:
                    # Store as (start_slot, list_of_8_slots, day)
                    full_days.append((slot_ids[0], slot_ids[:8], day))
        
        return full_days
    
    def create_variables(self, fixed_assignments=None):
        """Create decision variables with graduation project support."""
        print("Creating decision variables...")
        
        if fixed_assignments is None:
            fixed_assignments = {}
        
        skipped = []
        stats = {'lectures': 0, 'tutorials': 0, 'labs': 0, 'graduation_projects': 0}
        
        for course_code, course_info in self.courses.items():
            
            course_fixed = fixed_assignments.get(course_code, {})
            
            # GRADUATION PROJECTS (Special handling for 8-slot blocks)
            if course_info.get('is_graduation_project', False):
                instructors = self.get_instructors_for_course(course_code)
                
                if not instructors:
                    skipped.append(f"{course_code} GRAD_PROJECT (no instructors)")
                else:
                    groups = self.get_groups_for_course(course_code)
                    
                    if not groups:
                        skipped.append(f"{course_code} GRAD_PROJECT (no groups)")
                    else:
                        full_day_slots = self.get_full_day_slots()
                        
                        if not full_day_slots:
                            skipped.append(f"{course_code} GRAD_PROJECT (no full-day slots)")
                        else:
                            for group in groups:
                                group_id = f"Y{group['year']}_G{group['group_number']}"
                                student_count = group['total_students']
                                suitable_halls = self.get_suitable_halls('LEC', student_count, course_code)
                                
                                if not suitable_halls:
                                    continue
                                
                                # Create one variable per full-day slot
                                for start_slot, slot_list, day in full_day_slots:
                                    for hall in suitable_halls:
                                        for instructor in instructors:
                                            var_name = f"{course_code}_{group_id}_GRADPROJ_T{start_slot}_H{hall}_I{instructor}"
                                            var = self.model.NewBoolVar(var_name)
                                            
                                            self.session_vars[course_code].append({
                                                'var': var,
                                                'type': 'GRAD_PROJECT',
                                                'course': course_code,
                                                'group': group_id,
                                                'sections_in_group': [
                                                    f"Y{group['year']}_G{group['group_number']}_S{s['section']}" 
                                                    for s in group['sections']
                                                ],
                                                'session_num': 0,
                                                'slot': start_slot,
                                                'slot_list': slot_list,  # All 8 slots
                                                'day': day,
                                                'hall': hall,
                                                'instructor': instructor,
                                                'is_ta': False,
                                                'students': student_count
                                            })
                                            stats['graduation_projects'] += 1
            
            # REGULAR LECTURES
            elif course_info['lec_count'] > 0:
                instructors = self.get_instructors_for_course(course_code)
                
                if not instructors:
                    skipped.append(f"{course_code} LEC (no instructors)")
                else:
                    groups = self.get_groups_for_course(course_code)
                    
                    if not groups:
                        skipped.append(f"{course_code} LEC (no groups)")
                    else:
                        for group in groups:
                            group_id = f"Y{group['year']}_G{group['group_number']}"
                            student_count = group['total_students']
                            
                            for lec_num in range(course_info['lec_count']):
                                suitable_halls = self.get_suitable_halls('LEC', student_count, course_code)
                                
                                if not suitable_halls:
                                    continue
                                
                                for slot_id in range(len(self.timeslots) - 1):
                                    if self.is_consecutive_slot(slot_id, slot_id + 1):
                                        for hall in suitable_halls:
                                            for instructor in instructors:
                                                var_name = f"{course_code}_{group_id}_LEC{lec_num}_T{slot_id}_H{hall}_I{instructor}"
                                                var = self.model.NewBoolVar(var_name)
                                                
                                                self.session_vars[course_code].append({
                                                    'var': var,
                                                    'type': 'LEC',
                                                    'course': course_code,
                                                    'group': group_id,
                                                    'sections_in_group': [
                                                        f"Y{group['year']}_G{group['group_number']}_S{s['section']}" 
                                                        for s in group['sections']
                                                    ],
                                                    'session_num': lec_num,
                                                    'slot': slot_id,
                                                    'slot2': slot_id + 1,
                                                    'hall': hall,
                                                    'instructor': instructor,
                                                    'is_ta': False,
                                                    'students': student_count
                                                })
                                                stats['lectures'] += 1
            
            # TUTORIALS
            if course_info['tut_count'] > 0:
                tas = self.get_tas_for_course(course_code, 'TUT')
                
                if not tas:
                    skipped.append(f"{course_code} TUT (no TAs)")
                else:
                    sections = self.get_sections_for_course(course_code)
                    
                    if not sections:
                        skipped.append(f"{course_code} TUT (no sections)")
                    else:
                        needs_double_slot = (course_info['tut_duration'] >= 1.0)
                        
                        for section in sections:
                            section_id = f"Y{section['year']}_G{section['group']}_S{section['section']}"
                            student_count = section['students']
                            
                            for tut_num in range(course_info['tut_count']):
                                suitable_halls = self.get_suitable_halls('TUT', student_count, course_code)
                                
                                if not suitable_halls:
                                    continue
                                
                                if needs_double_slot:
                                    for slot_id in range(len(self.timeslots) - 1):
                                        if self.is_consecutive_slot(slot_id, slot_id + 1):
                                            for hall in suitable_halls:
                                                for ta in tas:
                                                    var_name = f"{course_code}_{section_id}_TUT{tut_num}_T{slot_id}_H{hall}_TA{ta}"
                                                    var = self.model.NewBoolVar(var_name)
                                                    
                                                    self.session_vars[course_code].append({
                                                        'var': var,
                                                        'type': 'TUT',
                                                        'course': course_code,
                                                        'section': section_id,
                                                        'session_num': tut_num,
                                                        'slot': slot_id,
                                                        'slot2': slot_id + 1,
                                                        'hall': hall,
                                                        'instructor': ta,
                                                        'is_ta': True,
                                                        'students': student_count
                                                    })
                                                    stats['tutorials'] += 1
                                else:
                                    for slot_id in range(len(self.timeslots)):
                                        for hall in suitable_halls:
                                            for ta in tas:
                                                var_name = f"{course_code}_{section_id}_TUT{tut_num}_T{slot_id}_H{hall}_TA{ta}"
                                                var = self.model.NewBoolVar(var_name)
                                                
                                                self.session_vars[course_code].append({
                                                    'var': var,
                                                    'type': 'TUT',
                                                    'course': course_code,
                                                    'section': section_id,
                                                    'session_num': tut_num,
                                                    'slot': slot_id,
                                                    'hall': hall,
                                                    'instructor': ta,
                                                    'is_ta': True,
                                                    'students': student_count
                                                })
                                                stats['tutorials'] += 1
            
            # LABS (same as before, skipping for brevity)
            if course_info['lab_count'] > 0:
                tas = self.get_tas_for_course(course_code, 'LAB')
                
                if not tas:
                    skipped.append(f"{course_code} LAB (no TAs)")
                else:
                    if course_code == 'PHY113':
                        groups = self.get_groups_for_course(course_code)
                        if not groups:
                            skipped.append(f"{course_code} LAB (no groups)")
                        else:
                            for group in groups:
                                group_id = f"Y{group['year']}_G{group['group_number']}"
                                student_count = group['total_students']
                                
                                for lab_num in range(course_info['lab_count']):
                                    suitable_halls = self.get_suitable_halls('LAB', student_count, course_code)
                                    
                                    if not suitable_halls:
                                        continue
                                    
                                    for slot_id in range(len(self.timeslots) - 1):
                                        if self.is_consecutive_slot(slot_id, slot_id + 1):
                                            for hall in suitable_halls:
                                                for ta in tas:
                                                    var_name = f"{course_code}_{group_id}_LAB{lab_num}_T{slot_id}_H{hall}_TA{ta}"
                                                    var = self.model.NewBoolVar(var_name)
                                                    
                                                    self.session_vars[course_code].append({
                                                        'var': var,
                                                        'type': 'LAB',
                                                        'course': course_code,
                                                        'group': group_id,
                                                        'sections_in_group': [
                                                            f"Y{group['year']}_G{group['group_number']}_S{s['section']}" 
                                                            for s in group['sections']
                                                        ],
                                                        'session_num': lab_num,
                                                        'slot': slot_id,
                                                        'slot2': slot_id + 1,
                                                        'hall': hall,
                                                        'instructor': ta,
                                                        'is_ta': True,
                                                        'students': student_count
                                                    })
                                                    stats['labs'] += 1
                    else:
                        sections = self.get_sections_for_course(course_code)
                        
                        if not sections:
                            skipped.append(f"{course_code} LAB (no sections)")
                        else:
                            for section in sections:
                                section_id = f"Y{section['year']}_G{section['group']}_S{section['section']}"
                                student_count = section['students']
                                
                                for lab_num in range(course_info['lab_count']):
                                    suitable_halls = self.get_suitable_halls('LAB', student_count, course_code)
                                    
                                    if not suitable_halls:
                                        continue
                                    
                                    for slot_id in range(len(self.timeslots) - 1):
                                        if self.is_consecutive_slot(slot_id, slot_id + 1):
                                            for hall in suitable_halls:
                                                for ta in tas:
                                                    var_name = f"{course_code}_{section_id}_LAB{lab_num}_T{slot_id}_H{hall}_TA{ta}"
                                                    var = self.model.NewBoolVar(var_name)
                                                    
                                                    self.session_vars[course_code].append({
                                                        'var': var,
                                                        'type': 'LAB',
                                                        'course': course_code,
                                                        'section': section_id,
                                                        'session_num': lab_num,
                                                        'slot': slot_id,
                                                        'slot2': slot_id + 1,
                                                        'hall': hall,
                                                        'instructor': ta,
                                                        'is_ta': True,
                                                        'students': student_count
                                                    })
                                                    stats['labs'] += 1
        
        total_vars = sum(len(sessions) for sessions in self.session_vars.values())
        print(f"Created {total_vars} decision variables")
        print(f"  - Lecture variables: {stats['lectures']}")
        print(f"  - Tutorial variables: {stats['tutorials']}")
        print(f"  - Lab variables: {stats['labs']}")
        print(f"  - Graduation project variables: {stats['graduation_projects']}")
        
        if skipped:
            print(f"Skipped sessions:")
            for skip_msg in skipped[:10]:
                print(f"  ✗ {skip_msg}")
            if len(skipped) > 10:
                print(f"  ... and {len(skipped) - 10} more")
    
    def add_hard_constraints(self):
        """Add hard constraints with graduation project support."""
        print("Adding hard constraints...")
        
        # 1. Each session scheduled exactly once
        for course_code, sessions in self.session_vars.items():
            by_identifier = defaultdict(list)
            
            for s in sessions:
                if s['type'] == 'GRAD_PROJECT':
                    key = (s['group'], s['type'], 0)  # Only one graduation project session
                elif s['type'] == 'LEC':
                    key = (s['group'], s['type'], s['session_num'])
                elif s['type'] == 'LAB' and course_code == 'PHY113':
                    key = (s['group'], s['type'], s['session_num'])
                else:
                    key = (s['section'], s['type'], s['session_num'])
                
                by_identifier[key].append(s['var'])
            
            for key, vars_list in by_identifier.items():
                self.model.Add(sum(vars_list) == 1)
        
        # 2. No room conflicts (including 8-slot graduation projects)
        sessions_by_hall_slot = defaultdict(list)
        
        for course_sessions in self.session_vars.values():
            for s in course_sessions:
                if s['type'] == 'GRAD_PROJECT':
                    # Mark all 8 slots as occupied
                    for slot in s['slot_list']:
                        sessions_by_hall_slot[(s['hall'], slot)].append(s['var'])
                else:
                    sessions_by_hall_slot[(s['hall'], s['slot'])].append(s['var'])
                    
                    if 'slot2' in s:
                        sessions_by_hall_slot[(s['hall'], s['slot2'])].append(s['var'])
        
        for vars_list in sessions_by_hall_slot.values():
            if len(vars_list) > 1:
                self.model.Add(sum(vars_list) <= 1)
        
        # 3. No instructor/TA conflicts
        sessions_by_instructor_slot = defaultdict(list)
        
        for course_sessions in self.session_vars.values():
            for s in course_sessions:
                if s['type'] == 'GRAD_PROJECT':
                    for slot in s['slot_list']:
                        sessions_by_instructor_slot[(s['instructor'], slot)].append(s['var'])
                else:
                    sessions_by_instructor_slot[(s['instructor'], s['slot'])].append(s['var'])
                    
                    if 'slot2' in s:
                        sessions_by_instructor_slot[(s['instructor'], s['slot2'])].append(s['var'])
        
        for vars_list in sessions_by_instructor_slot.values():
            if len(vars_list) > 1:
                self.model.Add(sum(vars_list) <= 1)
        
        # 4. No student conflicts
        for section in self.sections:
            section_id = f"Y{section['year']}_G{section['group']}_S{section['section']}"
            sessions_by_slot = defaultdict(list)
            
            for course_sessions in self.session_vars.values():
                for s in course_sessions:
                    affects_section = False
                    
                    if s['type'] == 'GRAD_PROJECT':
                        affects_section = section_id in s['sections_in_group']
                    elif s['type'] == 'LEC':
                        affects_section = section_id in s['sections_in_group']
                    elif s['type'] == 'LAB' and s['course'] == 'PHY113':
                        affects_section = section_id in s['sections_in_group']
                    else:
                        affects_section = s['section'] == section_id
                    
                    if affects_section:
                        if s['type'] == 'GRAD_PROJECT':
                            for slot in s['slot_list']:
                                sessions_by_slot[slot].append(s['var'])
                        else:
                            sessions_by_slot[s['slot']].append(s['var'])
                            
                            if 'slot2' in s:
                                sessions_by_slot[s['slot2']].append(s['var'])
            
            for slot_id, vars_list in sessions_by_slot.items():
                if len(vars_list) > 1:
                    self.model.Add(sum(vars_list) <= 1)
        
        print("Hard constraints added")
    
    def solve(self):
        """Solve the CSP problem."""
        print("\nSolving CSP...")
        print("=" * 50)
        
        start_time = time.time()
        status = self.solver.Solve(self.model)
        solve_time = time.time() - start_time
        
        print(f"\nSolver finished in {solve_time:.2f} seconds")
        print(f"Status: {self.solver.StatusName(status)}")
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            print(f"✓ Solution found!")
            print(f"  Branches: {self.solver.NumBranches()}")
            print(f"  Conflicts: {self.solver.NumConflicts()}")
            print(f"  Wall time: {self.solver.WallTime():.2f}s")
            return True
        else:
            print(f"✗ No feasible solution found")
            return False
    
    def export_timetable(self, output_file):
        """Export the generated timetable to Excel."""
        print(f"\nExporting timetable to {output_file}...")
        
        results = []
        
        for course_sessions in self.session_vars.values():
            for s in course_sessions:
                if self.solver.BooleanValue(s['var']):
                    slot = self.timeslots[s['slot']]
                    
                    if s.get('is_ta', False):
                        if s['instructor'] in self.tas:
                            instructor_name = self.tas[s['instructor']]['name']
                        else:
                            instructor_name = f"TA_{s['instructor']}"
                    else:
                        if s['instructor'] in self.instructors:
                            instructor_name = self.instructors[s['instructor']]['name']
                        else:
                            instructor_name = f"Instructor_{s['instructor']}"
                    
                    # Handle graduation projects (full day)
                    if s['type'] == 'GRAD_PROJECT':
                        end_slot = self.timeslots[s['slot_list'][-1]]
                        end_time = end_slot['end']
                        session_type = 'GRAD_PROJECT'
                    elif 'slot2' in s:
                        end_time = self.timeslots[s['slot2']]['end']
                        session_type = s['type']
                    else:
                        end_time = slot['end']
                        session_type = s['type']
                    
                    if s['type'] in ['LEC', 'GRAD_PROJECT'] or (s['type'] == 'LAB' and s['course'] == 'PHY113'):
                        group_section = s['group']
                    else:
                        group_section = s['section']
                    
                    result = {
                        'Course': s['course'],
                        'Group/Section': group_section,
                        'Type': session_type,
                        'Session': s['session_num'],
                        'Day': slot['day'],
                        'Start': slot['start'],
                        'End': end_time,
                        'Hall': s['hall'],
                        'Instructor/TA': instructor_name,
                        'Students': s['students']
                    }
                    
                    results.append(result)
        
        if len(results) == 0:
            print(f"⚠ WARNING: No sessions scheduled (empty timetable)")
            df = pd.DataFrame(columns=['Course', 'Group/Section', 'Type', 'Session', 
                                      'Day', 'Start', 'End', 'Hall', 'Instructor/TA', 'Students'])
        else:
            df = pd.DataFrame(results)
            df = df.sort_values(['Group/Section', 'Day', 'Start'])
        
        df.to_excel(output_file, index=False)
        
        print(f"✓ Timetable exported successfully!")
        print(f"  Total sessions scheduled: {len(results)}")
        
        return df
    
    def generate(self, output_file, fixed_assignments=None):
        """Main workflow to generate timetable."""
        spec_label = f" {self.target_specialization}" if self.target_specialization else ""
        print("=" * 50)
        print(f"CSIT TIMETABLE GENERATOR - Year {self.target_year}{spec_label}")
        print("=" * 50)
        
        self.load_data()
        
        if len(self.courses) == 0:
            print(f"\n⚠ WARNING: No courses found")
            print("Creating empty timetable file...")
            df = pd.DataFrame(columns=['Course', 'Group/Section', 'Type', 'Session', 
                                      'Day', 'Start', 'End', 'Hall', 'Instructor/TA', 'Students'])
            df.to_excel(output_file, index=False)
            return df, {}
        
        self.create_variables(fixed_assignments)
        self.add_hard_constraints()
        
        success = self.solve()
        
        if success:
            df = self.export_timetable(output_file)
            return df, {}
        else:
            print("\nFailed to generate timetable.")
            return None, {}


def main():
    """Generate timetables for all years with graduation project support."""
    print("\n" + "=" * 60)
    print("CSIT TIMETABLE GENERATOR - WITH GRADUATION PROJECT SUPPORT")
    print("=" * 60 + "\n")
    
    # Configuration
    configs = [
    (1, None, "output/timetable_year1.xlsx"),
    (2, None, "output/timetable_year2.xlsx"),
    (3, 'CSC', "output/timetable_year3_CSC.xlsx"),
    (3, 'AID', "output/timetable_year3_AID.xlsx"),
    (3, 'CNC', "output/timetable_year3_CNC.xlsx"),
    (3, 'BIF', "output/timetable_year3_BIF.xlsx"),
    (4, 'CSC', "output/timetable_year4_CSC.xlsx"),
    (4, 'AID', "output/timetable_year4_AID.xlsx"),
    (4, 'CNC', "output/timetable_year4_CNC.xlsx"),
    (4, 'BIF', "output/timetable_year4_BIF.xlsx"),
    ]

    
    results = {}
    
    for year, spec, output_file in configs:
        label = f"Year {year}" if spec is None else f"Year {year} {spec}"
        
        print(f"\n{'='*60}")
        print(f"PROCESSING {label.upper()}")
        print(f"{'='*60}\n")
        
        generator = CSITTimetableGenerator(target_year=year, target_specialization=spec)
        timetable, _ = generator.generate(output_file)
        
        results[(year, spec)] = timetable
        
        if timetable is not None:
            if len(timetable) > 0:
                print(f"\n✓ {label} timetable generated successfully!")
            else:
                print(f"\n⚠ {label} timetable is empty")
        else:
            print(f"\n✗ {label} timetable generation failed!")
        
        print("\n" + "=" * 60 + "\n")
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for df in results.values() if df is not None and len(df) > 0)
    total = len(results)
    print(f"\nSuccessfully generated: {successful}/{total} timetables\n")
    
    for year, spec, output_file in configs:
        df = results.get((year, spec))
        label = f"Year {year}" if spec is None else f"Year {year} {spec}"
        
        if df is not None:
            status = f"({len(df)} sessions)" if len(df) > 0 else "(EMPTY)"
            print(f"  ✓ {label}: {output_file} {status}")
        else:
            print(f"  ✗ {label}: FAILED")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    main()
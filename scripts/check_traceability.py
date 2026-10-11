import sys, pathlib

def check_traceability():
    root = pathlib.Path(__file__).resolve().parent.parent
    trac_file = root / "docs" / "qa" / "Requirements_Traceability.md"
    if not trac_file.exists():
        print(f"Error: {trac_file} not found")
        return 1

    content = trac_file.read_text()
    
    test_plan_file = root / "docs" / "qa" / "QA_Test_Plan.md"
    if not test_plan_file.exists():
        print("Error: QA_Test_Plan.md not found")
        return 1
        
    plan_content = test_plan_file.read_text()
    
    errors = 0
    
    for row in content.splitlines()[4:]:
        if not row.strip() or not row.startswith('|'): continue
        cells = [c.strip() for c in row.split('|')]
        if len(cells) < 7: continue
        
        # [1] is empty (the string split makes | id | look like ['', 'id', ''])
        case_id = cells[1]
        
        if not case_id.startswith('J') and not case_id.startswith('X') and not case_id.startswith('PT-') and not case_id.startswith('BB-'):
            continue
            
        if f"#### {case_id}" not in plan_content and f"| {case_id}" not in plan_content:
            print(f"Error: Case ID {case_id} found in traceability matrix but not in QA_Test_Plan.md")
            errors += 1
            
    if errors > 0:
        return 1
    return 0
    
if __name__ == "__main__":
    sys.exit(check_traceability())

import json

def load_csv_variables(analysis_file):
    with open(analysis_file, 'r') as f:
        data = json.load(f)
    csv_analysis = data.get('csv_analysis', {})
    variables = set()
    for var_info in csv_analysis.get('sample_variables', []):
        variables.add(var_info['value'].split(',')[0].strip()) # Extract variable name before comma
    return variables

def load_pdf_variables(pdf_text_file):
    with open(pdf_text_file, 'r') as f:
        content = f.read()
    
    variables = set()
    # Split content by lines and look for variable names
    # Assuming variable names are in the 'Name' column of the PDF table
    # This is a heuristic and might need adjustment based on PDF parsing accuracy
    lines = content.split('\n')
    in_variables_section = False
    for line in lines:
        line = line.strip()
        if line.startswith('ID') and 'Name' in line and 'Description' in line and 'Value' in line:
            in_variables_section = True
            continue
        if in_variables_section and line and not line.startswith('Job Number:') and not line.startswith('MiTek MBA for Pamir') and not line.startswith('Page '):
            parts = line.split(maxsplit=1) # Split only once to get ID and then Name/Description/Value
            if len(parts) > 1:
                # Heuristic: variable name is usually the second part, before description/value
                # This is fragile and might need manual verification
                name_part = parts[1].split(' ')[0].strip()
                if name_part and not name_part.isdigit(): # Ensure it's not just a number
                    variables.add(name_part)
    return variables

if __name__ == "__main__":
    csv_analysis_file = "/home/ubuntu/mitek_file_analysis.json"
    pdf_text_file = "/home/ubuntu/JobVariable.txt"

    csv_vars = load_csv_variables(csv_analysis_file)
    pdf_vars = load_pdf_variables(pdf_text_file)

    missing_in_csv = pdf_vars - csv_vars

    print("Variables in PDF but NOT in CSV:")
    if missing_in_csv:
        for var in sorted(list(missing_in_csv)):
            print(f"- {var}")
    else:
        print("No additional variables found in PDF compared to CSV.")

    print("\nCSV Variables (for reference):")
    for var in sorted(list(csv_vars)):
        print(f"- {var}")

    print("\nPDF Variables (for reference):")
    for var in sorted(list(pdf_vars)):
        print(f"- {var}")



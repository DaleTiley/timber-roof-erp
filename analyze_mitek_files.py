import pandas as pd
import openpyxl
import json
from pathlib import Path

def analyze_excel_file(file_path):
    """Analyze Excel file structure and content."""
    print(f"\n=== ANALYZING EXCEL FILE: {file_path} ===")
    
    try:
        # Load workbook to get sheet names
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet_names = workbook.sheetnames
        
        print(f"Number of sheets: {len(sheet_names)}")
        print(f"Sheet names: {sheet_names}")
        
        analysis = {}
        
        for sheet_name in sheet_names:
            print(f"\n--- SHEET: {sheet_name} ---")
            
            try:
                # Read sheet with pandas
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                
                print(f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
                
                # Show first few rows
                print("First 10 rows:")
                for i in range(min(10, df.shape[0])):
                    row_data = []
                    for j in range(min(10, df.shape[1])):
                        cell_value = df.iloc[i, j]
                        if pd.notna(cell_value):
                            row_data.append(str(cell_value))
                        else:
                            row_data.append("")
                    print(f"Row {i+1}: {row_data}")
                
                # Look for patterns that might be variables or data
                non_empty_cells = []
                for i in range(df.shape[0]):
                    for j in range(df.shape[1]):
                        cell_value = df.iloc[i, j]
                        if pd.notna(cell_value) and str(cell_value).strip():
                            non_empty_cells.append({
                                'row': i+1,
                                'col': j+1,
                                'value': str(cell_value).strip()
                            })
                
                print(f"Total non-empty cells: {len(non_empty_cells)}")
                
                # Store analysis
                analysis[sheet_name] = {
                    'dimensions': f"{df.shape[0]}x{df.shape[1]}",
                    'non_empty_cells': len(non_empty_cells),
                    'sample_data': non_empty_cells[:20]  # First 20 non-empty cells
                }
                
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {e}")
                analysis[sheet_name] = {'error': str(e)}
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")
        return {'error': str(e)}

def analyze_csv_file(file_path):
    """Analyze CSV file structure and content."""
    print(f"\n=== ANALYZING CSV FILE: {file_path} ===")
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, header=None)
                print(f"Successfully read with encoding: {encoding}")
                break
            except:
                continue
        
        if df is None:
            print("Could not read CSV file with any encoding")
            return {'error': 'Could not read CSV file'}
        
        print(f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Show first few rows
        print("First 20 rows:")
        for i in range(min(20, df.shape[0])):
            row_data = []
            for j in range(df.shape[1]):
                cell_value = df.iloc[i, j]
                if pd.notna(cell_value):
                    row_data.append(str(cell_value))
                else:
                    row_data.append("")
            print(f"Row {i+1}: {row_data}")
        
        # Look for variable patterns
        variables = []
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                cell_value = df.iloc[i, j]
                if pd.notna(cell_value):
                    cell_str = str(cell_value).strip()
                    # Look for patterns that might be variable names
                    if any(keyword in cell_str.upper() for keyword in ['LENGTH', 'AREA', 'WIDTH', 'HEIGHT', 'ANGLE', 'COUNT', 'QTY']):
                        variables.append({
                            'row': i+1,
                            'col': j+1,
                            'value': cell_str
                        })
        
        print(f"\nPotential variables found: {len(variables)}")
        for var in variables[:10]:  # Show first 10
            print(f"  Row {var['row']}, Col {var['col']}: {var['value']}")
        
        return {
            'dimensions': f"{df.shape[0]}x{df.shape[1]}",
            'potential_variables': len(variables),
            'sample_variables': variables[:20]
        }
        
    except Exception as e:
        print(f"Error analyzing CSV file: {e}")
        return {'error': str(e)}

def main():
    # File paths
    excel_file = "/home/ubuntu/upload/S04002-5.xlsm"
    csv_file = "/home/ubuntu/upload/S04002-5.csv"
    
    # Analyze both files
    excel_analysis = analyze_excel_file(excel_file)
    csv_analysis = analyze_csv_file(csv_file)
    
    # Save analysis to JSON for reference
    analysis_result = {
        'excel_analysis': excel_analysis,
        'csv_analysis': csv_analysis
    }
    
    with open('/home/ubuntu/mitek_file_analysis.json', 'w') as f:
        json.dump(analysis_result, f, indent=2, default=str)
    
    print(f"\n=== ANALYSIS COMPLETE ===")
    print("Analysis saved to: /home/ubuntu/mitek_file_analysis.json")
    print("\nNow you can explain what's important from each sheet and how it should be stored!")

if __name__ == "__main__":
    main()


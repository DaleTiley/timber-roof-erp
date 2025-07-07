import pandas as pd
import uuid
from datetime import datetime
from src.models.project_hierarchy import ProjectVariable
from src.models.user import db

class MitekImportService:
    """Service for importing Mitek Pamir variables from CSV/Excel files"""
    
    @staticmethod
    def parse_csv_file(file_path):
        """Parse Mitek Pamir CSV file and extract variables"""
        variables = []
        
        try:
            # Read CSV file - Mitek format is: VARIABLE_NAME,VALUE,UNIT
            df = pd.read_csv(file_path, header=None, names=['variable_name', 'value', 'unit'])
            
            for _, row in df.iterrows():
                variable = {
                    'variable_name': row['variable_name'].strip(),
                    'variable_value': str(row['value']).strip(),
                    'variable_unit': row['unit'].strip() if pd.notna(row['unit']) else '',
                    'variable_category': MitekImportService._categorize_variable(row['variable_name'])
                }
                variables.append(variable)
                
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
            
        return variables
    
    @staticmethod
    def parse_excel_file(file_path):
        """Parse Mitek Pamir Excel file and extract variables"""
        variables = []
        
        try:
            # Read Excel file - try different sheet names that Mitek might use
            possible_sheets = ['Variables', 'Data', 'Export', 'Sheet1']
            df = None
            
            for sheet_name in possible_sheets:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                    break
                except:
                    continue
            
            if df is None:
                # Try reading the first sheet
                df = pd.read_excel(file_path, header=None)
            
            # Assume format is: VARIABLE_NAME,VALUE,UNIT
            df.columns = ['variable_name', 'value', 'unit']
            
            for _, row in df.iterrows():
                if pd.notna(row['variable_name']) and pd.notna(row['value']):
                    variable = {
                        'variable_name': str(row['variable_name']).strip(),
                        'variable_value': str(row['value']).strip(),
                        'variable_unit': str(row['unit']).strip() if pd.notna(row['unit']) else '',
                        'variable_category': MitekImportService._categorize_variable(str(row['variable_name']))
                    }
                    variables.append(variable)
                    
        except Exception as e:
            raise Exception(f"Error parsing Excel file: {str(e)}")
            
        return variables
    
    @staticmethod
    def _categorize_variable(variable_name):
        """Categorize variables based on their names"""
        variable_name = variable_name.upper()
        
        # Length/Distance measurements
        if any(keyword in variable_name for keyword in ['LENGTH', 'LINE', 'WALLPLATE', 'BRACING', 'BATTEN', 'EAVES', 'RIDGE', 'HIP', 'VALLEY', 'GABLE']):
            return 'DIMENSION'
        
        # Area measurements
        elif any(keyword in variable_name for keyword in ['AREA', 'ROOF_AREA', 'CEILING_AREA', 'FLOOR_AREA']):
            return 'AREA'
        
        # Count/Quantity measurements
        elif any(keyword in variable_name for keyword in ['COUNT', 'PCS', 'INTERSECTS', 'CLIPS', 'CORNERS', 'STRAPS']):
            return 'COUNT'
        
        # Angle measurements
        elif any(keyword in variable_name for keyword in ['ANGLE', 'PITCH', 'SLOPE']):
            return 'ANGLE'
        
        # Weight measurements
        elif any(keyword in variable_name for keyword in ['WEIGHT', 'LOAD']):
            return 'WEIGHT'
        
        # Default category
        else:
            return 'OTHER'
    
    @staticmethod
    def import_variables_to_project(project_id, quote_id, variables, mitek_job_number, user_id):
        """Import variables to a specific project and quote"""
        try:
            # Generate batch ID for this import
            batch_id = str(uuid.uuid4())
            
            # Clear existing variables for this quote if re-importing
            if quote_id:
                ProjectVariable.query.filter_by(quote_id=quote_id).delete()
            
            # Import new variables
            imported_count = 0
            for var_data in variables:
                variable = ProjectVariable(
                    project_id=project_id,
                    quote_id=quote_id,
                    variable_name=var_data['variable_name'],
                    variable_value=var_data['variable_value'],
                    variable_unit=var_data['variable_unit'],
                    variable_category=var_data['variable_category'],
                    import_batch_id=batch_id,
                    mitek_job_number=mitek_job_number,
                    imported_by=user_id
                )
                db.session.add(variable)
                imported_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'batch_id': batch_id,
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} variables'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to import variables: {str(e)}'
            }
    
    @staticmethod
    def get_variable_summary(variables):
        """Get a summary of variables by category"""
        summary = {}
        
        for variable in variables:
            category = variable['variable_category']
            if category not in summary:
                summary[category] = {
                    'count': 0,
                    'variables': []
                }
            
            summary[category]['count'] += 1
            summary[category]['variables'].append({
                'name': variable['variable_name'],
                'value': variable['variable_value'],
                'unit': variable['variable_unit']
            })
        
        return summary
    
    @staticmethod
    def validate_mitek_file(file_path):
        """Validate that the file contains expected Mitek Pamir data"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=None, nrows=10)
            else:
                df = pd.read_excel(file_path, header=None, nrows=10)
            
            # Check if we have at least 3 columns
            if len(df.columns) < 2:
                return False, "File must have at least 2 columns (variable name and value)"
            
            # Check if first column contains variable names (should be strings)
            first_col_sample = df.iloc[:, 0].dropna().head(5)
            if first_col_sample.empty:
                return False, "No data found in first column"
            
            # Check if variable names look like Mitek variables
            mitek_keywords = ['EAVES', 'RIDGE', 'AREA', 'LENGTH', 'COUNT', 'TRUSS', 'BATTEN']
            has_mitek_vars = any(
                any(keyword in str(var).upper() for keyword in mitek_keywords)
                for var in first_col_sample
            )
            
            if not has_mitek_vars:
                return False, "File doesn't appear to contain Mitek Pamir variables"
            
            return True, "File validation successful"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"


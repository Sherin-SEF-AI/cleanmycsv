import pandas as pd
import groq
from typing import Dict, Optional
import re
import json
from app.config import settings

class CSVCleaner:
    def __init__(self):
        if settings.GROQ_API_KEY:
            self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
        else:
            self.groq_client = None
    
    def clean_data(self, df: pd.DataFrame, user_instructions: str = "", basic_only: bool = False) -> Dict:
        """Main cleaning function with optional LLM features"""
        
        # Initial quality assessment and issue detection
        initial_quality = self.calculate_quality_score(df)
        initial_issues = self.detect_issues(df)
        
        cleaning_report = {
            'original_rows': len(df),
            'original_columns': len(df.columns),
            'operations_performed': [],
            'data_quality_score_before': initial_quality,
            'issues_found': initial_issues
        }
        
        # 1. Basic cleaning (always applied)
        df = self.remove_empty_rows(df)
        cleaning_report['operations_performed'].append("Removed empty rows")
        
        df = self.remove_duplicates(df)
        cleaning_report['operations_performed'].append("Removed duplicates")
        
        df = self.basic_type_conversion(df)
        cleaning_report['operations_performed'].append("Basic type conversion")
        
        # 2. LLM-powered features (only for registered users or when basic_only=False)
        if not basic_only and self.groq_client:
            try:
                # Smart column analysis
                column_analysis = self.analyze_columns_with_llm(df)
                cleaning_report['column_analysis'] = column_analysis
                
                # Apply column-specific cleaning
                for col, col_type in column_analysis.items():
                    if col_type == 'email':
                        df[col] = self.clean_emails(df[col])
                        cleaning_report['operations_performed'].append(f"Cleaned emails in '{col}'")
                    elif col_type == 'phone':
                        df[col] = self.clean_phone_numbers(df[col])
                        cleaning_report['operations_performed'].append(f"Standardized phones in '{col}'")
                    elif col_type == 'date':
                        df[col] = self.clean_dates(df[col])
                        cleaning_report['operations_performed'].append(f"Standardized dates in '{col}'")
                    elif col_type == 'currency':
                        df[col] = self.clean_currency(df[col])
                        cleaning_report['operations_performed'].append(f"Cleaned currency in '{col}'")
                
                # Process user instructions
                if user_instructions:
                    df = self.apply_user_instructions(df, user_instructions)
                    cleaning_report['operations_performed'].append(f"Applied custom instructions: {user_instructions}")
                    
            except Exception as e:
                cleaning_report['llm_error'] = str(e)
        
        # 3. Final quality assessment
        cleaning_report.update({
            'final_rows': len(df),
            'final_columns': len(df.columns),
            'data_quality_score_after': self.calculate_quality_score(df),
            'rows_removed': cleaning_report['original_rows'] - len(df)
        })
        
        return {
            'cleaned_data': df,
            'report': cleaning_report
        }
    
    def analyze_columns_with_llm(self, df: pd.DataFrame) -> Dict[str, str]:
        """Use LLM to detect column types and suggest cleaning"""
        if not self.groq_client:
            return {}
            
        column_types = {}
        
        for col in df.columns:
            if df[col].dtype == 'object':  # Only analyze text columns
                sample_values = df[col].dropna().head(3).tolist()
                if not sample_values:
                    continue
                    
                try:
                    response = self.groq_client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{
                            "role": "user",
                            "content": f"Column '{col}' has values: {sample_values}. What type? Answer ONE word: email, phone, date, name, address, currency, url, or text"
                        }],
                        max_tokens=5,
                        temperature=0
                    )
                    
                    col_type = response.choices[0].message.content.strip().lower()
                    column_types[col] = col_type
                    
                except Exception as e:
                    column_types[col] = 'text'  # Fallback
        
        return column_types
    
    def apply_user_instructions(self, df: pd.DataFrame, instructions: str) -> pd.DataFrame:
        """Convert natural language instructions to pandas operations"""
        if not self.groq_client:
            return df
        
        prompt = f"""
        DataFrame info: {len(df)} rows, columns: {list(df.columns)}
        User wants: "{instructions}"
        
        Write Python pandas code using 'df' variable. Return ONLY code, no explanations.
        
        Examples:
        "remove duplicates" → df.drop_duplicates()
        "fix phone format" → df['phone'] = df['phone'].str.replace(r'[^\\d]', '', regex=True)
        "standardize dates" → df['date'] = pd.to_datetime(df['date'], errors='coerce')
        "remove rows where age > 100" → df = df[df['age'] <= 100]
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0
            )
            
            code = response.choices[0].message.content.strip()
            
            # Basic safety check
            if any(dangerous in code.lower() for dangerous in ['import', 'exec', 'eval', 'open', 'file']):
                return df
            
            # Execute the generated code
            exec(code)
            return df
            
        except Exception as e:
            return df  # Return original if LLM fails
    
    # Basic cleaning methods
    def remove_empty_rows(self, df):
        return df.dropna(how='all')
    
    def remove_duplicates(self, df):
        return df.drop_duplicates()
    
    def basic_type_conversion(self, df):
        """Convert obvious numeric columns"""
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                converted = pd.to_numeric(df[col], errors='coerce')
                if converted.notna().sum() > len(df) * 0.7:  # 70% conversion success
                    df[col] = converted
        return df
    
    def clean_emails(self, series):
        return series.str.lower().str.strip()
    
    def clean_phone_numbers(self, series):
        """Extract digits and format as (XXX) XXX-XXXX"""
        def format_phone(phone):
            if pd.isna(phone):
                return phone
            digits = re.sub(r'\D', '', str(phone))
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            return digits
        
        return series.apply(format_phone)
    
    def clean_dates(self, series):
        return pd.to_datetime(series, errors='coerce')
    
    def clean_currency(self, series):
        """Remove currency symbols and convert to float"""
        def clean_money(value):
            if pd.isna(value):
                return value
            cleaned = re.sub(r'[$,€£¥]', '', str(value))
            try:
                return float(cleaned)
            except:
                return value
        
        return series.apply(clean_money)
    
    def detect_issues(self, df):
        """Detect common data quality issues"""
        issues = []
        
        # Check for empty rows
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            issues.append(f"{empty_rows} completely empty rows found")
        
        # Check for duplicate rows
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            issues.append(f"{duplicate_rows} duplicate rows found")
        
        # Check for columns with high null percentage
        for col in df.columns:
            null_percentage = df[col].isnull().sum() / len(df) * 100
            if null_percentage > 50:
                issues.append(f"Column '{col}' has {null_percentage:.1f}% missing values")
        
        # Check for potential data type issues
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check for mixed data types in object columns
                sample_values = df[col].dropna().head(10)
                if len(sample_values) > 0:
                    # Try to detect if it should be numeric
                    numeric_count = pd.to_numeric(sample_values, errors='coerce').notna().sum()
                    if numeric_count > len(sample_values) * 0.7:
                        issues.append(f"Column '{col}' contains numeric data but is stored as text")
        
        return issues
    
    def calculate_quality_score(self, df):
        """Calculate comprehensive data quality percentage"""
        if df.empty:
            return 0
        
        total_cells = df.size
        quality_factors = []
        
        # Factor 1: Completeness (non-null values)
        null_cells = df.isnull().sum().sum()
        completeness = (total_cells - null_cells) / total_cells
        quality_factors.append(completeness * 0.4)  # 40% weight
        
        # Factor 2: Uniqueness (no duplicates)
        duplicate_rows = df.duplicated().sum()
        uniqueness = 1 - (duplicate_rows / len(df)) if len(df) > 0 else 1
        quality_factors.append(uniqueness * 0.3)  # 30% weight
        
        # Factor 3: Consistency (data type consistency)
        consistency_score = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if object column could be better typed
                sample_values = df[col].dropna().head(20)
                if len(sample_values) > 0:
                    # Try numeric conversion
                    numeric_count = pd.to_numeric(sample_values, errors='coerce').notna().sum()
                    if numeric_count > len(sample_values) * 0.8:
                        consistency_score += 0.5  # Penalty for mis-typed numeric data
                    else:
                        consistency_score += 1.0
                else:
                    consistency_score += 1.0
            else:
                consistency_score += 1.0
        
        consistency = consistency_score / len(df.columns) if len(df.columns) > 0 else 1
        quality_factors.append(consistency * 0.2)  # 20% weight
        
        # Factor 4: Validity (basic format checks)
        validity_score = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check for extremely long strings (potential data corruption)
                max_length = df[col].astype(str).str.len().max()
                if max_length < 1000:  # Reasonable string length
                    validity_score += 1.0
                else:
                    validity_score += 0.5
            else:
                validity_score += 1.0
        
        validity = validity_score / len(df.columns) if len(df.columns) > 0 else 1
        quality_factors.append(validity * 0.1)  # 10% weight
        
        # Calculate final score
        final_score = sum(quality_factors) * 100
        return round(max(0, min(100, final_score)), 1) 
#!/usr/bin/env python3
"""
Company Valuations CSV Loader

This utility loads ForgeGlobal company pricing data from CSV files into the company_valuations table.
It handles parsing of composite pricing data, date extraction, and validation.

Usage:
    python -m source_code.utils.company_valuations_loader --file path/to/csv/file.csv
    python -m source_code.utils.company_valuations_loader --directory path/to/csv/directory
    python -m source_code.utils.company_valuations_loader --auto-discover
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import the models and CRUD operations
try:
    from source_code.models.models import CompanyValuationDtlInput
    from source_code.crud.company_valuations_crud_operations import company_valuation_crud
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)


class CompanyValuationsLoader:
    """Loader for ForgeGlobal CSV files to company_valuations table."""

    def __init__(self, price_source: str = "ForgeGlobal"):
        self.price_source = price_source
        self.loaded_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.errors: List[str] = []

    def load_csv_file(self, file_path: str, as_of_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Load a single CSV file into the company_valuations table.
        
        Args:
            file_path: Path to the CSV file
            as_of_date: Date to use for the data. If None, extracts from filename or uses today.
            
        Returns:
            Dictionary with loading results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Extract date from filename if not provided
        if as_of_date is None:
            as_of_date = self._extract_date_from_filename(file_path)

        print(f"Loading CSV file: {file_path}")
        print(f"Using as_of_date: {as_of_date}")

        results = {
            'file': file_path,
            'as_of_date': as_of_date.isoformat(),
            'loaded': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Validate headers
                if not self._validate_headers(reader.fieldnames):
                    raise ValueError("CSV file does not have expected headers")
                
                row_num = 1  # Header is row 1
                for row in reader:
                    row_num += 1
                    try:
                        company_valuation = self._parse_csv_row(row, as_of_date)
                        if company_valuation:
                            # Save to database
                            company_valuation_crud.save(company_valuation)
                            results['loaded'] += 1
                            self.loaded_count += 1
                        else:
                            results['skipped'] += 1
                            self.skipped_count += 1
                    except Exception as e:
                        error_msg = f"Row {row_num}: {str(e)}"
                        results['error_details'].append(error_msg)
                        results['errors'] += 1
                        self.error_count += 1
                        self.errors.append(error_msg)
                        print(f"Error processing {error_msg}")

        except Exception as e:
            raise RuntimeError(f"Failed to process CSV file {file_path}: {str(e)}")

        print(f"Completed loading {file_path}: {results['loaded']} loaded, {results['skipped']} skipped, {results['errors']} errors")
        return results

    def load_directory(self, directory_path: str, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Load all CSV files from a directory.
        
        Args:
            directory_path: Path to directory containing CSV files
            as_of_date: Date to use for all files. If None, extracts from each filename.
            
        Returns:
            List of result dictionaries for each file
        """
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"Directory not found: {directory_path}")

        csv_files = []
        for file_name in os.listdir(directory_path):
            if file_name.lower().endswith('.csv') and 'forge_companies' in file_name.lower():
                csv_files.append(os.path.join(directory_path, file_name))

        if not csv_files:
            print(f"No ForgeGlobal CSV files found in directory: {directory_path}")
            return []

        print(f"Found {len(csv_files)} CSV files to process")
        
        results = []
        for csv_file in sorted(csv_files):
            try:
                result = self.load_csv_file(csv_file, as_of_date)
                results.append(result)
            except Exception as e:
                error_result = {
                    'file': csv_file,
                    'loaded': 0,
                    'skipped': 0,
                    'errors': 1,
                    'error_details': [f"Failed to process file: {str(e)}"]
                }
                results.append(error_result)
                self.error_count += 1
                self.errors.append(f"File {csv_file}: {str(e)}")
                print(f"Failed to process {csv_file}: {str(e)}")

        return results

    def auto_discover_and_load(self) -> List[Dict[str, Any]]:
        """
        Auto-discover CSV files in the samples directory and load them.
        
        Returns:
            List of result dictionaries for each file
        """
        # Look for CSV files in the samples directory relative to this script
        script_dir = Path(__file__).parent
        samples_dir = script_dir / "samples"
        
        if not samples_dir.exists():
            print(f"Samples directory not found: {samples_dir}")
            return []

        return self.load_directory(str(samples_dir))

    def _validate_headers(self, headers: Optional[List[str]]) -> bool:
        """Validate that the CSV has the expected headers."""
        if not headers:
            return False
        
        # Convert to lowercase for case-insensitive comparison
        headers_lower = [h.lower().strip() for h in headers]
        
        # Required headers (case-insensitive)
        required_headers = {'company'}  # Minimum required
        expected_headers = {
            'company', 'sector & subsector', 'forge price1', 'last matched price',
            'share class', 'post-money valuation2', 'price per share', 'amount raised'
        }
        
        # Check if we have the minimum required headers
        return required_headers.issubset(set(headers_lower))

    def _extract_date_from_filename(self, file_path: str) -> date:
        """
        Extract date from filename like 'forge_companies_20251008_192333.csv'.
        Returns today's date if no date pattern is found.
        """
        filename = os.path.basename(file_path)
        
        # Pattern: forge_companies_YYYYMMDD_HHMMSS.csv
        pattern = r'forge_companies_(\d{8})_\d{6}\.csv'
        match = re.search(pattern, filename, re.IGNORECASE)
        
        if match:
            date_str = match.group(1)
            try:
                return datetime.strptime(date_str, '%Y%m%d').date()
            except ValueError:
                pass
        
        # Fallback: try other date patterns in filename
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
            r'(\d{8})',              # YYYYMMDD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1).replace('_', '-')
                try:
                    if len(date_str) == 8:  # YYYYMMDD
                        return datetime.strptime(date_str, '%Y%m%d').date()
                    else:  # YYYY-MM-DD
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue
        
        # Default to today if no date found
        print(f"Warning: Could not extract date from filename {filename}, using today's date")
        return date.today()

    def _parse_csv_row(self, row: Dict[str, str], as_of_date: date) -> Optional[CompanyValuationDtlInput]:
        """
        Parse a CSV row into a CompanyValuationDtlInput object.
        
        Args:
            row: Dictionary representing a CSV row
            as_of_date: Date to assign to this valuation
            
        Returns:
            CompanyValuationDtlInput object or None if row should be skipped
        """
        # Get company name - skip if empty
        company = self._get_csv_value(row, 'company')
        if not company or company.strip() == '':
            return None  # Skip empty rows
        
        # Parse the Forge Price1 composite field
        forge_price_raw = self._get_csv_value(row, 'forge price1')
        price, price_change_amt, price_change_perc = self._parse_forge_price(forge_price_raw)
        
        # Get other fields
        sector_subsector = self._get_csv_value(row, 'sector & subsector')
        last_matched_price = self._get_csv_value(row, 'last matched price')
        share_class = self._get_csv_value(row, 'share class')
        post_money_valuation = self._get_csv_value(row, 'post-money valuation2')
        price_per_share_raw = self._get_csv_value(row, 'price per share')
        amount_raised = self._get_csv_value(row, 'amount raised')
        
        # Parse price_per_share as float if possible
        price_per_share = self._parse_float(price_per_share_raw)
        
        # Create raw_data_json with the original row data
        raw_data_json = dict(row)
        
        return CompanyValuationDtlInput(
            as_of_date=as_of_date,
            price_source=self.price_source,
            company=company.strip(),
            sector_subsector=sector_subsector.strip() if sector_subsector else None,
            price=price,
            price_change_amt=price_change_amt,
            price_change_perc=price_change_perc,
            last_matched_price=last_matched_price.strip() if last_matched_price else None,
            share_class=share_class.strip() if share_class else None,
            post_money_valuation=post_money_valuation.strip() if post_money_valuation else None,
            price_per_share=price_per_share,
            amount_raised=amount_raised.strip() if amount_raised else None,
            raw_data_json=raw_data_json
        )

    def _get_csv_value(self, row: Dict[str, str], column_name: str) -> str:
        """Get a value from CSV row, handling case-insensitive column names."""
        # Try exact match first
        if column_name in row:
            return row[column_name] or ''
        
        # Try case-insensitive match
        column_lower = column_name.lower()
        for key, value in row.items():
            if key.lower() == column_lower:
                return value or ''
        
        return ''

    def _parse_forge_price(self, forge_price_text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Parse the composite Forge Price field like '$723.12 +$253.65 (54.03%)'.
        
        Returns:
            Tuple of (price, change_amount, change_percentage)
        """
        if not forge_price_text or forge_price_text.strip() in ['--', '']:
            return None, None, None
        
        text = forge_price_text.strip()
        
        # Extract base price (first monetary amount)
        price_match = re.search(r'\$?([\d,]+\.?\d*)', text)
        price = None
        if price_match:
            try:
                price = float(price_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        # Extract change amount (signed monetary amount)
        change_match = re.search(r'([+-])\$?([\d,]+\.?\d*)', text)
        change_amount = None
        if change_match:
            try:
                sign = 1 if change_match.group(1) == '+' else -1
                amount = float(change_match.group(2).replace(',', ''))
                change_amount = sign * amount
            except ValueError:
                pass
        
        # Extract percentage change
        perc_match = re.search(r'\(([\d.+-]+)%\)', text)
        change_perc = None
        if perc_match:
            try:
                change_perc = float(perc_match.group(1))
            except ValueError:
                pass
        
        return price, change_amount, change_perc

    def _parse_float(self, value: str) -> Optional[float]:
        """Parse a string value to float, handling common formats."""
        if not value or value.strip() in ['--', '']:
            return None
        
        # Clean the value
        clean_value = value.strip().replace(',', '').replace('$', '')
        
        try:
            return float(clean_value)
        except ValueError:
            return None

    def print_summary(self):
        """Print a summary of the loading operation."""
        print("\n" + "="*60)
        print("COMPANY VALUATIONS LOADER SUMMARY")
        print("="*60)
        print(f"Total loaded: {self.loaded_count}")
        print(f"Total skipped: {self.skipped_count}")
        print(f"Total errors: {self.error_count}")
        
        if self.errors:
            print(f"\nErrors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")


def main():
    """Command-line interface for the loader."""
    parser = argparse.ArgumentParser(description="Load ForgeGlobal CSV data into company_valuations table")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='Path to a single CSV file to load')
    group.add_argument('--directory', help='Path to directory containing CSV files to load')
    group.add_argument('--auto-discover', action='store_true', help='Auto-discover CSV files in samples directory')
    
    parser.add_argument('--date', help='Override date for all records (YYYY-MM-DD format)')
    parser.add_argument('--price-source', default='ForgeGlobal', help='Price source name (default: ForgeGlobal)')
    
    args = parser.parse_args()
    
    # Parse date if provided
    as_of_date = None
    if args.date:
        try:
            as_of_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
            return 1
    
    # Create loader
    loader = CompanyValuationsLoader(price_source=args.price_source)
    
    try:
        results = []
        
        if args.file:
            result = loader.load_csv_file(args.file, as_of_date)
            results.append(result)
        elif args.directory:
            results = loader.load_directory(args.directory, as_of_date)
        elif args.auto_discover:
            results = loader.auto_discover_and_load()
        
        # Print summary
        loader.print_summary()
        
        return 0 if loader.error_count == 0 else 1
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
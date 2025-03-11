"""Module for formatting paper results into CSV or console output."""

import csv
import io
import sys
import logging
from typing import Dict, List, Any, Optional, TextIO

import pandas as pd

logger = logging.getLogger(__name__)

class OutputFormatter:
    """Format paper results into CSV or console output."""
    
    def __init__(self):
        """Initialize formatter."""
        pass
    
    def format_as_csv(
        self, papers: List[Dict[str, Any]], output_file: Optional[str] = None
    ) -> Optional[str]:
        """
        Format papers as CSV data.
        
        Args:
            papers: List of paper dictionaries
            output_file: Optional file path to save CSV; if None, returns CSV as string
            
        Returns:
            CSV string if output_file is None, otherwise None
        """
        if not papers:
            logger.warning("No papers to format")
            return "" if output_file is None else None
        
        # Define CSV columns with the required order
        columns = [
            "pubmed_id", "title", "publication_date", 
            "non_academic_authors", "company_affiliations", 
            "corresponding_author_email"
        ]
        
        # Rename for CSV header
        column_mapping = {
            "pubmed_id": "PubmedID",
            "title": "Title",
            "publication_date": "Publication Date",
            "non_academic_authors": "Non-academic Author(s)",
            "company_affiliations": "Company Affiliation(s)",
            "corresponding_author_email": "Corresponding Author Email"
        }
        
        try:
            # Create DataFrame from papers
            df = pd.DataFrame(papers)
            
            # Ensure all required columns exist
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Select and order columns
            df = df[columns]
            
            # Rename columns for CSV header
            df = df.rename(columns=column_mapping)
            
            if output_file:
                # Save to file
                df.to_csv(output_file, index=False)
                logger.info(f"Results saved to {output_file}")
                return None
            else:
                # Return as string
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                return csv_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"Error formatting CSV: {str(e)}")
            if output_file is None:
                return ""
            return None
    
    def print_results(self, papers: List[Dict[str, Any]]) -> None:
        """
        Print paper results to console in a readable format.
        
        Args:
            papers: List of paper dictionaries
        """
        if not papers:
            print("No matching papers found.")
            return
        
        print(f"\nFound {len(papers)} papers with pharma/biotech company affiliations:\n")
        
        for i, paper in enumerate(papers, 1):
            print(f"--- Paper {i} ---")
            print(f"PubMed ID: {paper.get('pubmed_id', 'N/A')}")
            print(f"Title: {paper.get('title', 'N/A')}")
            print(f"Publication Date: {paper.get('publication_date', 'N/A')}")
            print(f"Non-academic Author(s): {paper.get('non_academic_authors', 'N/A')}")
            print(f"Company Affiliation(s): {paper.get('company_affiliations', 'N/A')}")
            print(f"Corresponding Author Email: {paper.get('corresponding_author_email', 'N/A')}")
            print("")
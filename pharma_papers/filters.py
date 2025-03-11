"""Module for filtering papers based on author affiliations."""

import re
import logging
from typing import Dict, List, Any, Set, Optional, Tuple

logger = logging.getLogger(__name__)

class AffiliationFilter:
    """Filter for identifying pharmaceutical and biotech company affiliations."""
    
    # Common academic institution keywords
    ACADEMIC_KEYWORDS = {
        'university', 'college', 'institute', 'school', 'academy', 
        'faculty', 'department', 'laboratory', 'hospital', 'clinic',
        'medical center', 'health system', 'polytechnic', 'academia'
    }
    
    # Government and non-profit organization keywords
    GOVT_NONPROFIT_KEYWORDS = {
        'ministry', 'department of', 'national institute', 'foundation',
        'association', 'society', 'center for', 'organization', 'trust',
        'council', 'agency', 'authority', 'public health', 'government',
        'federal', 'state', 'county', 'committee', 'administration'
    }
    
    # Pharma/biotech specific keywords
    PHARMA_BIOTECH_KEYWORDS = {
        'pharma', 'biotech', 'therapeutics', 'bioscience',
        'laboratories', 'labs', 'biotechnology', 'pharmaceutical',
        'biopharmaceutical', 'genetics', 'genomics', 'life sciences',
        'biologics', 'medicines', 'drugs', ' ltd', ' llc', ' inc', ' corp',
        'therapeutics', 'diagnostics', ' gmbh', ' co', 'biopharma'
    }
    
    # Email domain patterns for academic institutions
    ACADEMIC_EMAIL_PATTERNS = [
        r'\.edu$', r'\.edu\.\w+$', r'\.ac\.\w+$', r'\.sch\.\w+$',
        r'\.university\.\w+$', r'\.institute\.\w+$'
    ]
    
    def __init__(self):
        """Initialize the filter with default settings."""
        pass
    
    def filter_papers_with_company_affiliations(
        self, papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter papers to include only those with at least one author 
        from a pharmaceutical or biotech company.
        
        Args:
            papers: List of paper dictionaries from parser
        
        Returns:
            Filtered list of papers with company affiliation data added
        """
        filtered_papers = []
        
        for paper in papers:
            pharma_authors = []
            company_affiliations = set()
            
            # Process each author
            for author in paper.get("authors", []):
                is_non_academic, affiliations = self._check_author_affiliations(author)
                
                if is_non_academic:
                    pharma_authors.append(author["name"])
                    company_affiliations.update(affiliations)
            
            # Only include papers with at least one pharma/biotech author
            if pharma_authors:
                paper_data = {
                    "pubmed_id": paper.get("pubmed_id", ""),
                    "title": paper.get("title", ""),
                    "publication_date": paper.get("publication_date", ""),
                    "non_academic_authors": ", ".join(pharma_authors),
                    "company_affiliations": ", ".join(company_affiliations),
                    "corresponding_author_email": paper.get("corresponding_author_email", "")
                }
                filtered_papers.append(paper_data)
        
        logger.debug(f"Filtered {len(filtered_papers)} papers with company affiliations")
        return filtered_papers
    
    def _check_author_affiliations(
        self, author: Dict[str, Any]
    ) -> Tuple[bool, Set[str]]:
        """
        Check if an author is affiliated with a pharmaceutical or biotech company.
        
        Args:
            author: Author dictionary with name and affiliations
        
        Returns:
            Tuple of (is_non_academic, company_names)
        """
        if not author.get("affiliations"):
            return False, set()
        
        company_names = set()
        has_academic_affiliation = False
        has_company_affiliation = False
        
        for affiliation in author.get("affiliations", []):
            affiliation_lower = affiliation.lower()
            
            # Skip if empty affiliation
            if not affiliation_lower.strip():
                continue
            
            # Check for academic keywords
            if any(keyword in affiliation_lower for keyword in self.ACADEMIC_KEYWORDS):
                has_academic_affiliation = True
                continue
                
            # Check for government/non-profit keywords
            if any(keyword in affiliation_lower for keyword in self.GOVT_NONPROFIT_KEYWORDS):
                continue
            
            # Check for pharma/biotech keywords
            if any(keyword in affiliation_lower for keyword in self.PHARMA_BIOTECH_KEYWORDS):
                has_company_affiliation = True
                # Extract company name using heuristics
                company_name = self._extract_company_name(affiliation)
                if company_name:
                    company_names.add(company_name)
        
        # If author has both academic and company affiliations, they're considered mixed
        # We still want to include them in our results
        is_non_academic = has_company_affiliation
        
        return is_non_academic, company_names
    
    def _extract_company_name(self, affiliation: str) -> str:
        """
        Extract company name from affiliation string using heuristics.
        
        Args:
            affiliation: Complete affiliation string
        
        Returns:
            Extracted company name or original affiliation if extraction fails
        """
        # Common company suffixes
        company_suffixes = [
            'Inc.', 'LLC', 'Ltd.', 'Limited', 'Corp.', 'Corporation',
            'GmbH', 'Co.', 'Company', 'S.A.', 'AG', 'B.V.'
        ]
        
        # Try to extract company name using suffixes
        for suffix in company_suffixes:
            if suffix in affiliation:
                # Find the part before the suffix
                parts = affiliation.split(suffix)
                if parts and parts[0]:
                    # Take the last segment before suffix, which is likely the company name
                    name_parts = parts[0].split(',')
                    company = name_parts[-1].strip()
                    if company:
                        return f"{company} {suffix}".strip()
        
        # If suffix-based extraction fails, use a simpler approach
        # Take the first segment, which often contains the company name
        first_segment = affiliation.split(',')[0].strip()
        
        # Limit length to avoid overly long strings
        if len(first_segment) > 50:
            first_segment = first_segment[:47] + "..."
            
        return first_segment
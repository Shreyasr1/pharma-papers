"""Module for interacting with the PubMed API."""

import time
from typing import Dict, List, Optional, Any, Union
import logging
import urllib.parse

import requests

logger = logging.getLogger(__name__)

class PubMedAPI:
    """Class to interact with the PubMed API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, tool: str = "pharma_papers", email: str = "user@example.com"):
        """
        Initialize PubMed API client.
        
        Args:
            tool: Name of the tool making requests (for NCBI tracking)
            email: Contact email (required by NCBI for heavy usage)
        """
        self.tool = tool
        self.email = email
    
    def search(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search PubMed for articles matching the query.
        
        Args:
            query: PubMed search query
            max_results: Maximum number of results to return
        
        Returns:
            List of PubMed IDs matching the query
        
        Raises:
            requests.RequestException: If the API request fails
        """
        logger.debug(f"Searching PubMed with query: {query}")
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # First get the list of PMIDs
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": encoded_query,
            "retmax": max_results,
            "retmode": "json",
            "tool": self.tool,
            "email": self.email
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            result = response.json()
            
            pmids = result.get("esearchresult", {}).get("idlist", [])
            logger.debug(f"Found {len(pmids)} papers matching the query")
            
            return pmids
        except requests.RequestException as e:
            logger.error(f"Error searching PubMed: {e}")
            raise
    
    def fetch_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed information for a list of PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs to fetch details for
        
        Returns:
            List of dictionaries containing paper details
        
        Raises:
            requests.RequestException: If the API request fails
        """
        if not pmids:
            logger.warning("No PMIDs provided to fetch_details")
            return []
        
        logger.debug(f"Fetching details for {len(pmids)} papers")
        
        # Use the efetch API to get detailed XML data
        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        
        # Process in batches to avoid large requests
        batch_size = 50
        all_papers = []
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i+batch_size]
            pmids_str = ",".join(batch_pmids)
            
            params = {
                "db": "pubmed",
                "id": pmids_str,
                "retmode": "xml",
                "tool": self.tool,
                "email": self.email
            }
            
            try:
                response = requests.get(fetch_url, params=params)
                response.raise_for_status()
                
                # Return raw XML for parsing in the parser module
                all_papers.append(response.text)
                
                # Be respectful to the API - don't make requests too quickly
                if i + batch_size < len(pmids):
                    time.sleep(0.5)
                    
            except requests.RequestException as e:
                logger.error(f"Error fetching paper details: {e}")
                raise
        
        logger.debug(f"Successfully fetched details for {len(pmids)} papers")
        return all_papers
"""Module for parsing PubMed API responses."""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

class PubMedParser:
    """Parser for PubMed API responses."""
    
    def parse_xml_batch(self, xml_data: str) -> List[Dict[str, Any]]:
        """
        Parse XML data from PubMed efetch API.
        
        Args:
            xml_data: XML data from PubMed efetch API
        
        Returns:
            List of dictionaries containing paper information
        """
        papers = []
        
        try:
            root = ET.fromstring(xml_data)
            article_elements = root.findall(".//PubmedArticle")
            
            for article in article_elements:
                try:
                    paper_info = self._extract_paper_info(article)
                    if paper_info:
                        papers.append(paper_info)
                except Exception as e:
                    pmid = article.find(".//PMID")
                    pmid_text = pmid.text if pmid is not None and pmid.text else "unknown"
                    logger.error(f"Error parsing paper {pmid_text}: {str(e)}")
            
            return papers
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return []
    
    def _extract_paper_info(self, article: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Extract paper information from a PubmedArticle XML element.
        
        Args:
            article: PubmedArticle XML element
        
        Returns:
            Dictionary containing paper information or None if extraction fails
        """
        try:
            # Extract PMID
            pmid_elem = article.find(".//PMID")
            if pmid_elem is None or not pmid_elem.text:
                logger.warning("Paper missing PMID, skipping")
                return None
            
            pmid = pmid_elem.text
            
            # Extract title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None and title_elem.text else "Unknown Title"
            
            # Extract publication date
            pub_date = self._extract_publication_date(article)
            
            # Extract authors with affiliations
            authors_with_affiliations = self._extract_authors(article)
            
            # Extract corresponding author email
            corresponding_author_email = self._extract_corresponding_email(article)
            
            return {
                "pubmed_id": pmid,
                "title": title,
                "publication_date": pub_date,
                "authors": authors_with_affiliations,
                "corresponding_author_email": corresponding_author_email
            }
        
        except Exception as e:
            logger.error(f"Error extracting paper info: {str(e)}")
            return None
    
    def _extract_publication_date(self, article: ET.Element) -> str:
        """Extract publication date from article."""
        try:
            pub_date_elem = article.find(".//PubDate")
            if pub_date_elem is None:
                return "Unknown Date"
            
            year_elem = pub_date_elem.find("Year")
            month_elem = pub_date_elem.find("Month")
            day_elem = pub_date_elem.find("Day")
            
            year = year_elem.text if year_elem is not None and year_elem.text else "????"
            month = month_elem.text if month_elem is not None and month_elem.text else "??"
            day = day_elem.text if day_elem is not None and day_elem.text else "??"
            
            # Convert month name to number if needed
            month_map = {
                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
            }
            
            if month in month_map:
                month = month_map[month]
            
            if year != "????":
                if month != "??" and day != "??":
                    return f"{year}-{month}-{day}"
                elif month != "??":
                    return f"{year}-{month}"
                else:
                    return year
            
            return "Unknown Date"
        
        except Exception as e:
            logger.error(f"Error extracting publication date: {str(e)}")
            return "Unknown Date"
    
    def _extract_authors(self, article: ET.Element) -> List[Dict[str, Any]]:
        """Extract authors with their affiliations."""
        authors = []
        
        try:
            author_list = article.find(".//AuthorList")
            if author_list is None:
                return []
            
            for author_elem in author_list.findall("Author"):
                last_name_elem = author_elem.find("LastName")
                fore_name_elem = author_elem.find("ForeName")
                
                if last_name_elem is None or last_name_elem.text is None:
                    continue
                
                last_name = last_name_elem.text
                fore_name = fore_name_elem.text if fore_name_elem is not None and fore_name_elem.text else ""
                
                name = f"{fore_name} {last_name}".strip()
                
                # Extract affiliations
                affiliations = []
                
                # Check for AffiliationInfo elements (newer PubMed format)
                affiliation_infos = author_elem.findall(".//AffiliationInfo")
                if affiliation_infos:
                    for aff_info in affiliation_infos:
                        aff_elem = aff_info.find("Affiliation")
                        if aff_elem is not None and aff_elem.text:
                            affiliations.append(aff_elem.text)
                
                # Check for direct Affiliation element (older PubMed format)
                direct_aff = author_elem.find("Affiliation")
                if direct_aff is not None and direct_aff.text:
                    affiliations.append(direct_aff.text)
                
                authors.append({
                    "name": name,
                    "affiliations": affiliations
                })
            
            return authors
        
        except Exception as e:
            logger.error(f"Error extracting authors: {str(e)}")
            return []
    
    def _extract_corresponding_email(self, article: ET.Element) -> str:
        """Extract corresponding author email from article."""
        try:
            # Look in several possible locations
            
            # First, check in the ArticleId elements
            for id_elem in article.findall(".//ArticleId"):
                if id_elem.get("IdType") == "email":
                    return id_elem.text if id_elem.text else ""
            
            # Next, look in the Affiliation texts for email patterns
            for aff in article.findall(".//Affiliation"):
                if aff.text:
                    # Simple email regex pattern
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', aff.text)
                    if email_match:
                        return email_match.group(0)
            
            # Look in the ELocationID elements
            for eloc in article.findall(".//ELocationID"):
                if eloc.get("EIdType") == "email":
                    return eloc.text if eloc.text else ""
            
            # Look in the FootnoteList for correspondence info
            for footnote in article.findall(".//FootnoteList/Footnote"):
                if footnote.text and ("correspondence" in footnote.text.lower() or "email" in footnote.text.lower()):
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', footnote.text)
                    if email_match:
                        return email_match.group(0)
            
            return ""
        
        except Exception as e:
            logger.error(f"Error extracting corresponding email: {str(e)}")
            return ""
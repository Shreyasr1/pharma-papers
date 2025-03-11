"""Command-line interface for fetching research papers with company affiliations."""

import sys
import logging
from typing import Optional

import typer

from pharma_papers.api import PubMedAPI
from pharma_papers.parser import PubMedParser
from pharma_papers.filters import AffiliationFilter
from pharma_papers.formatter import OutputFormatter

# Create the CLI app
app = typer.Typer(
    help="Fetch research papers with authors affiliated with pharmaceutical companies"
)

# Set up logging
logger = logging.getLogger("pharma_papers")


@app.command()
def main(
    query: str = typer.Argument(..., help="PubMed search query"),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Output file path for CSV results"
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Enable debug logging"
    ),
    max_results: int = typer.Option(
        100, "--max", "-m", help="Maximum number of results to process"
    ),
):
    """
    Fetch research papers based on a query and identify those with
    pharmaceutical or biotech company affiliations.
    """
    # Set up logging based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    try:
        # Initialize components
        pubmed_api = PubMedAPI()
        parser = PubMedParser()
        affiliation_filter = AffiliationFilter()
        formatter = OutputFormatter()
        
        # Show what we're doing
        logger.info(f"Searching for papers matching: {query}")
        logger.info(f"Maximum results set to: {max_results}")
        
        # Step 1: Search for papers
        pmids = pubmed_api.search(query, max_results=max_results)
        if not pmids:
            logger.warning("No papers found matching the query")
            print("No papers found matching the query.")
            return
        
        # Step 2: Fetch paper details
        paper_xmls = pubmed_api.fetch_details(pmids)
        
        # Step 3: Parse paper details
        all_papers = []
        for xml_data in paper_xmls:
            papers = parser.parse_xml_batch(xml_data)
            all_papers.extend(papers)
        
        logger.info(f"Successfully parsed details for {len(all_papers)} papers")
        
        # Step 4: Filter papers with company affiliations
        filtered_papers = affiliation_filter.filter_papers_with_company_affiliations(all_papers)
        
        logger.info(f"Found {len(filtered_papers)} papers with pharmaceutical/biotech affiliations")
        
        # Step 5: Format and output results
        if file:
            formatter.format_as_csv(filtered_papers, file)
            print(f"Results saved to {file}")
        else:
            formatter.print_results(filtered_papers)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    app()
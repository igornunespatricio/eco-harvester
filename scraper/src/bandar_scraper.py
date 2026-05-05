import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import requests
import logging
from datetime import datetime
from .base_request_handler import BaseRequestHandler

dir = Path(__file__).parent.parent.parent
print(dir)
sys.path.append(str(dir))
print("Current sys.path:", sys.path)

from utils.storage_client import MinioS3Client

logger = logging.getLogger(__name__)


class BandarScraper(BaseRequestHandler):
    """
    Concrete implementation for scraping Bandar report export endpoint.
    Extends BaseRequestHandler abstract class.
    Handles CSRF token extraction, session management and report export.
    """

    REPORT_PATH = "/bandar/report"
    EXPORT_PATH = "/bandar/report/export"

    def __init__(self, **kwargs: Any):
        """Initialize Bandar scraper with correct base URL."""
        super().__init__(
            base_url="https://libgeo.univali.br",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
                "Origin": "https://libgeo.univali.br",
                "Referer": "https://libgeo.univali.br/bandar/report",
            },
            verify_ssl=False,
            **kwargs,
        )
        self.authenticity_token: Optional[str] = None

    def authenticate(self) -> None:
        """
        Implements abstract authenticate method.
        Loads the report page to establish session cookies and extract authenticity token.
        This is required before making any export requests.
        """
        logger.info("Authenticating: Loading report page to get session and CSRF token")

        response = self.get(self.REPORT_PATH)
        self._extract_authenticity_token(response.text)

        logger.info("Successfully authenticated and obtained authenticity token")

    def _extract_authenticity_token(self, html_content: str) -> None:
        """Extract Rails CSRF authenticity token from page HTML."""
        soup = BeautifulSoup(html_content, "lxml")
        token_input = soup.find("input", {"name": "authenticity_token"})

        if not token_input or not token_input.get("value"):
            raise ValueError("Could not find authenticity_token on report page")

        self.authenticity_token = token_input["value"]
        logger.debug(f"Extracted authenticity token: {self.authenticity_token[:20]}...")

    def handle_rate_limit(self, response: requests.Response) -> None:
        """Implements abstract rate limit handling for Bandar endpoint."""
        retry_after = int(response.headers.get("Retry-After", 60))
        logger.warning(f"Rate limited. Retry after: {retry_after} seconds")
        # Can implement actual waiting logic here if needed

    def _check_has_results(self, html_content: str) -> bool:
        """Check if the report page returned any results."""
        soup = BeautifulSoup(html_content, "lxml")
        no_results = soup.find("p", {"class": "no-results-label"})
        return no_results is None

    def export_report(
        self,
        date_start: datetime,
        date_end: datetime,
        animals: Optional[str] = "all_records",
        basins: Optional[str] = "all_records",
        form: Optional[str] = "RA",
        per: Optional[str] = "",
    ) -> Optional[bytes]:
        """
        Export report as XLSX file bytes.
        Must call authenticate() first before using this method.
        Returns None if no data is available for the given filters.

        Args:
            date_start: Start date for report
            date_end: End date for report
            animals: List of animal species names to filter, or "all_records" for no filtering
            basins: List of basin IDs to filter, or "all_records" for no filtering
            form: Report form type
            per: Pagination items per page parameter for API

        Returns:
            Raw XLSX file bytes

        Example:
            >>> from datetime import datetime
            >>> client.authenticate()
            >>> xlsx_bytes = client.export_report(
            ...     date_start=datetime(2025, 7, 1),
            ...     date_end=datetime(2025, 7, 3),
            ...     animals="Megaptera novaeangliae,Eubalaena australis,Balaenoptera edeni",
            ...     basins="0,1,2",
            ... )
            >>> with open("report.xlsx", "wb") as f:
            ...     f.write(xlsx_bytes)
        """
        if not self.authenticity_token:
            raise RuntimeError("Not authenticated. Call authenticate() first")

        base_payload = {
            "utf8": "✓",
            "authenticity_token": self.authenticity_token,
            "search[form]": form,
            "search[animal]": animals,
            "search[basin]": basins,
            "search[started]": date_start.strftime("%d/%m/%Y"),
            "search[finished]": date_end.strftime("%d/%m/%Y"),
            "search[occurrence]": "",
            "search[project]": "",
            "search[per]": per,
        }

        shared_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{self.base_url}{self.REPORT_PATH}",
        }

        # Pre-flight: check if any results exist before attempting export
        logger.info("Checking for available results before export...")
        search_response = self.post(
            self.REPORT_PATH,
            data={**base_payload, "search[action]": "Searchform"},
            headers=shared_headers,
        )

        if not self._check_has_results(search_response.text):
            logger.info(
                f"No results found for {date_start:%d/%m/%Y} to {date_end:%d/%m/%Y} "
                f"(animals={animals}, basins={basins}). Skipping export."
            )
            return None

        logger.info(
            f"Exporting report from {date_start:%d/%m/%Y} to {date_end:%d/%m/%Y}"
        )

        # Results exist — proceed with export
        response = self.post(
            self.EXPORT_PATH,
            data={**base_payload, "search[action]": "Exportform"},
            headers=shared_headers,
        )

        file_size = len(response.content)
        logger.info(f"Successfully downloaded report. File size: {file_size:,} bytes")

        return response.content

    def save_report(self, output_path: str, **kwargs: Any) -> None:
        """Export report and save directly to file."""
        content = self.export_report(**kwargs)
        with open(output_path, "wb") as f:
            f.write(content)
        logger.info(f"Report saved to {output_path}")


if __name__ == "__main__":
    date_from = datetime(2025, 6, 15)
    date_to = datetime(2025, 6, 15)

    animals = "Megaptera novaeangliae,Eubalaena australis"

    basins = "1,2,3"

    logger.info("Starting Bandar report export")

    # Using context manager for automatic session cleanup
    with BandarScraper() as scraper:
        try:
            # Step 1: Load page, get cookies and CSRF token
            scraper.authenticate()

            # Step 2: Export report
            xlsx_bytes = scraper.export_report(
                date_start=date_from, date_end=date_to, animals=animals, basins=basins
            )

            # Save to file
            output_filename = (
                f"bandar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            # with open(output_filename, "wb") as f:
            #     f.write(xlsx_bytes)
            import os

            storage_client = MinioS3Client(
                endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            )
            from io import BytesIO

            fileobj = (
                BytesIO(xlsx_bytes) if isinstance(xlsx_bytes, bytes) else xlsx_bytes
            )
            storage_client.upload_fileobj(
                fileobj=fileobj,
                bucket_name="raw",
                key=output_filename,
            )

            logger.info(f"Report successfully saved as: {output_filename}")

        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise

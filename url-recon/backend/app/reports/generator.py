from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.models.result import ScanResult
from app.storage.scan_store import SCANS_DIR


class PdfGenerationUnavailableError(RuntimeError):
    """Raised when PDF generation dependencies are not available."""

# Point Jinja2 at our templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def get_pdf_generation_status() -> tuple[bool, str | None]:
    """
    Checks whether WeasyPrint and its native dependencies are available.
    Returns a boolean plus an optional error string for diagnostics.
    """
    try:
        from weasyprint import HTML as WeasyHTML  # noqa: F401
    except (ImportError, OSError) as exc:
        return False, str(exc)

    return True, None


def _render_html(result: ScanResult) -> str:
    """
    Renders the Jinja2 template with the scan result data.
    Returns the rendered HTML as a string.
    We pass the entire ScanResult object into the template
    so every section can access any field it needs directly
    using dot notation — result.ssl.grade, result.whois.registrar etc.
    """
    template = env.get_template("report.html")
    return template.render(result=result)


def generate_html_report(result: ScanResult) -> Path:
    """
    Writes the rendered HTML report to disk.
    Returns the path so the API endpoint can serve it
    as a file download response.
    """
    output_dir = SCANS_DIR / result.meta.id
    output_dir.mkdir(parents=True, exist_ok=True)

    html_content = _render_html(result)
    output_path = output_dir / "report.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


def generate_pdf_report(result: ScanResult) -> Path:
    """
    Converts the rendered HTML to PDF using WeasyPrint.
    WeasyPrint renders HTML and CSS exactly as a browser would,
    then produces a pixel-perfect PDF from the result.
    No headless browser, no external dependencies beyond WeasyPrint.

    The PDF is saved alongside the HTML report in the scan directory.
    Returns the path so the API endpoint can serve it for download.
    """
    output_dir = SCANS_DIR / result.meta.id
    output_dir.mkdir(parents=True, exist_ok=True)

    html_content = _render_html(result)
    output_path = output_dir / "report.pdf"

    try:
        from weasyprint import HTML as WeasyHTML
    except (ImportError, OSError) as exc:
        raise PdfGenerationUnavailableError(
            "PDF generation is unavailable because WeasyPrint system libraries are missing."
        ) from exc

    # WeasyHTML takes the raw HTML string and base_url tells
    # WeasyPrint where to resolve any relative asset paths from
    WeasyHTML(
        string=html_content,
        base_url=str(output_dir),
    ).write_pdf(str(output_path))

    return output_path

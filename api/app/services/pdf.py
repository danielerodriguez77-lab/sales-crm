from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "storage" / "quotes"


env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html", "xml"])
)


def generate_quote_pdf(quote, customer_name: str, items: list[dict]) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    template = env.get_template("quote.html")
    html_content = template.render(quote=quote, customer_name=customer_name, items=items)

    filename = f"quote-{quote.id}-v{quote.version}.pdf"
    output_path = OUTPUT_DIR / filename
    HTML(string=html_content).write_pdf(str(output_path))
    return str(output_path)

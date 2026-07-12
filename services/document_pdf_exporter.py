# Document Engine v1 — PDF export utility.

from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def render_template(content_template: str, variables: dict[str, str]) -> str:
    rendered = content_template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    rendered = re.sub(r"\{\{[^}]+\}\}", "", rendered)
    return rendered


def content_to_pdf_bytes(
    *,
    title: str,
    content: str,
    reference_number: str,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 6 * mm),
        Paragraph(f"Reference: {reference_number}", styles["Normal"]),
        Spacer(1, 10 * mm),
    ]

    for line in content.splitlines():
        text = line.strip()
        if not text:
            story.append(Spacer(1, 3 * mm))
            continue
        if text.startswith("# "):
            story.append(Paragraph(text[2:], styles["Heading1"]))
        elif text.startswith("## "):
            story.append(Paragraph(text[3:], styles["Heading2"]))
        else:
            story.append(Paragraph(text, styles["Normal"]))
        story.append(Spacer(1, 2 * mm))

    doc.build(story)
    return buffer.getvalue()


def export_pdf_to_file(
    *,
    output_dir: str | Path,
    reference_number: str,
    title: str,
    content: str,
) -> tuple[str, bytes]:
    pdf_bytes = content_to_pdf_bytes(
        title=title,
        content=content,
        reference_number=reference_number,
    )
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_ref = re.sub(r"[^\w\-]", "_", reference_number)
    file_path = directory / f"{safe_ref}.pdf"
    file_path.write_bytes(pdf_bytes)
    return str(file_path), pdf_bytes


def signature_hash(content: str, signer_name: str, signed_at_iso: str) -> str:
    payload = f"{content}|{signer_name}|{signed_at_iso}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

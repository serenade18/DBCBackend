import io

import qrcode
import qrcode.image.svg
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def generate_qr_png(url: str) -> bytes:
    img = qrcode.make(url, box_size=10, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_svg(url: str) -> bytes:
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(url, image_factory=factory, box_size=10, border=2)
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue()


def generate_qr_pdf(url: str) -> bytes:
    png_bytes = generate_qr_png(url)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A6)
    width, height = A6
    size = 80 * mm
    x = (width - size) / 2
    y = (height - size) / 2
    from reportlab.lib.utils import ImageReader

    pdf.drawImage(ImageReader(io.BytesIO(png_bytes)), x, y, width=size, height=size)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


FORMAT_GENERATORS = {
    "png": (generate_qr_png, "image/png"),
    "svg": (generate_qr_svg, "image/svg+xml"),
    "pdf": (generate_qr_pdf, "application/pdf"),
}


def generate_qr_for_vcard(vcard, fmt: str = "png") -> tuple[bytes, str]:
    if fmt not in FORMAT_GENERATORS:
        raise ValueError(f"Unsupported QR format: {fmt}")
    generator, content_type = FORMAT_GENERATORS[fmt]
    return generator(vcard.public_url), content_type

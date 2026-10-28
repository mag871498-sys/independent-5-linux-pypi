"""Build an eight-page report from real Linux and packaging screenshots."""
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
EVIDENCE = REPORTS / "evidence"
OUTPUT = REPORTS / "output" / "pdf"
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
WIDTH = A4[0] - 144

pdfmetrics.registerFont(TTFont("TNR", str(FONT_DIR / "Times New Roman.ttf")))
pdfmetrics.registerFont(TTFont("TNR-Bold", str(FONT_DIR / "Times New Roman Bold.ttf")))
pdfmetrics.registerFontFamily(
    "TNR", normal="TNR", bold="TNR-Bold", italic="TNR", boldItalic="TNR-Bold"
)

STYLES = {
    "title": ParagraphStyle(
        "title", fontName="TNR-Bold", fontSize=16, leading=20,
        textColor=colors.black, alignment=TA_CENTER, spaceAfter=10,
    ),
    "section": ParagraphStyle(
        "section", fontName="TNR-Bold", fontSize=16, leading=20,
        textColor=colors.black, spaceAfter=10, keepWithNext=True,
    ),
    "body": ParagraphStyle(
        "body", fontName="TNR", fontSize=14, leading=18,
        textColor=colors.black, spaceAfter=10,
    ),
    "table": ParagraphStyle(
        "table", fontName="TNR", fontSize=14, leading=17,
        textColor=colors.black,
    ),
    "table_head": ParagraphStyle(
        "table_head", fontName="TNR-Bold", fontSize=14, leading=17,
        textColor=colors.black,
    ),
}

CONTEXT = "Debian ARM64 у Docker Desktop; sshd працює як ssh.service."
GITHUB_URL = "https://github.com/mag871498-sys/independent-5-linux-pypi"
PAGES = [
    {
        "heading": "1. Системні журнали",
        "images": [("journal.png", 240), ("ssh.png", 240)],
    },
    {
        "heading": "2. I/O та диски",
        "images": [("iostat.png", 220), ("disks.png", 190)],
        "after": [
            "IOPS - операції/с; пропускна здатність - обсяг даних/с.",
            "Виміряно активність віртуального диска Docker Desktop.",
            "fdisk підтримує GPT/MBR; parted має resizepart та сценарний режим -s. "
            "resizepart не змінює файлову систему.",
        ],
    },
    {
        "heading": "3. systemd-сервіс",
        "images": [("unit-code.png", 250), ("service-run.png", 300)],
        "after": [
            "WorkingDirectory=/opt/mytest задає поточний каталог процесу. Абсолютний /tmp/test.log від нього не залежить.",
        ],
    },
    {
        "heading": "4. Збірка пакета",
        "images": [("package-code.png", 280), ("build.png", 280)],
    },
    {
        "heading": "5. Локальний PyPI",
        "images": [("upload.png", 290), ("install.png", 290)],
    },
    {
        "heading": "6. CHANGELOG та формати",
        "images": [("changelog.png", 330)],
        "comparison": True,
        "after": [
            "CHANGELOG пов'язує версію зі змінами та допомагає перевіряти релізи й відкат.",
        ],
    },
    {
        "heading": "7. Molotov",
        "images": [("load-code.png", 260), ("load-run.png", 300)],
    },
    {
        "heading": "8. GitHub",
        "before": [GITHUB_URL],
        "images": [("github.png", 540)],
    },
]
COMPARISON = [
    ["Ознака", ".deb", ".rpm"],
    ["Інструменти", "dpkg / APT", "RPM / DNF"],
    ["Структура", "ar: control.tar, data.tar", "Заголовки та cpio"],
    ["Залежності", "control: Depends", "SPEC: Requires"],
]


def markdown_source():
    lines = ["# Самостійна робота №5", "", "# Linux та локальний PyPI", "", CONTEXT, ""]
    for page in PAGES:
        lines.extend(["## " + page["heading"], ""])
        for value in page.get("before", []):
            lines.extend([value, ""])
        for filename, _ in page["images"]:
            lines.extend([f"![](evidence/{filename})", ""])
        if page.get("comparison"):
            lines.append("| " + " | ".join(COMPARISON[0]) + " |")
            lines.append("| --- | --- | --- |")
            for row in COMPARISON[1:]:
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")
        for value in page.get("after", []):
            lines.extend([value, ""])
    return "\n".join(lines)


def build_report():
    missing = [
        name for page in PAGES for name, _ in page["images"]
        if not (EVIDENCE / name).is_file()
    ]
    if missing:
        raise FileNotFoundError("Missing evidence: " + ", ".join(missing))
    story = []

    def text(value, kind):
        story.append(Paragraph(escape(value), STYLES[kind]))

    def evidence(filename, max_height):
        source = EVIDENCE / filename
        with PILImage.open(source) as image:
            width, height = image.size
        scale = min(WIDTH / width, max_height / height)
        figure = Image(str(source), width=width * scale, height=height * scale)
        figure.hAlign = "CENTER"
        story.append(KeepTogether([figure, Spacer(1, 13)]))

    def comparison():
        rows = [
            [Paragraph(escape(value), STYLES["table_head" if index == 0 else "table"])
             for value in row]
            for index, row in enumerate(COMPARISON)
        ]
        table = Table(rows, colWidths=[100, (WIDTH - 100) / 2, (WIDTH - 100) / 2])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([KeepTogether([table, Spacer(1, 10)])])

    text("Самостійна робота №5", "title")
    text("Linux та локальний PyPI", "title")
    text(CONTEXT, "body")
    for index, page in enumerate(PAGES):
        if index:
            story.append(PageBreak())
        text(page["heading"], "section")
        for value in page.get("before", []):
            text(value, "body")
        for filename, max_height in page["images"]:
            evidence(filename, max_height)
        if page.get("comparison"):
            comparison()
        for value in page.get("after", []):
            text(value, "body")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    pdf = OUTPUT / "Самостійна_робота_5.pdf"
    SimpleDocTemplate(
        str(pdf), pagesize=A4,
        leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72,
        title="Самостійна робота №5. Linux та локальний PyPI", author="", pageCompression=1,
    ).build(story)
    (REPORTS / "Самостійна_робота_5.md").write_text(markdown_source(), encoding="utf-8")
    print(pdf)


if __name__ == "__main__":
    build_report()

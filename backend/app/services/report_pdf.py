"""The downloadable PDF report for a review. Built from the same data as the results page."""

from datetime import timezone

from fpdf import FPDF, XPos, YPos

from app.schemas import ReviewDetail

STATUS_LABELS = {"met": "Met", "partially_met": "Partially met", "not_met": "Not met"}
SUGGESTION_SECTIONS = [("add", "Missing (Add)"), ("change", "Change"), ("delete", "Delete")]
STATE_LABELS = {"open": "Open", "done": "Done", "dismissed": "Dismissed"}

# The PDF's built-in font only covers basic Western characters, so swap the common "smart" ones.
REPLACEMENTS = {
    "–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...", "→": "->", "•": "-", "✓": "v", "✗": "x", " ": " ", "≤": "<=", "≥": ">=",
}

GREEN = (12, 120, 12)
RED = (190, 40, 40)
AMBER = (170, 110, 0)
GREY = (100, 110, 120)
DARK = (20, 25, 35)


def _clean(text) -> str:
    text = "" if text is None else str(text)
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


class _Report(FPDF):
    def __init__(self, footer_text: str):
        super().__init__(format="A4")
        self.footer_text = footer_text
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY)
        self.cell(0, 5, _clean(f"{self.footer_text}   |   Page {self.page_no()}"), align="C")

    # Small helpers so the layout code below reads top to bottom.
    def heading(self, text, size=13):
        self.ln(3)
        self.set_font("Helvetica", "B", size)
        self.set_text_color(*DARK)
        self.multi_cell(0, 7, _clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def para(self, text, size=10, style="", color=DARK, height=5):
        self.set_font("Helvetica", style, size)
        self.set_text_color(*color)
        self.multi_cell(0, height, _clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def label_value(self, label, value):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GREY)
        self.cell(38, 5, _clean(label))
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5, _clean(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def rule_line(self):
        self.set_draw_color(220, 224, 230)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)


def _points(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def build_report(review: ReviewDetail) -> bytes:
    """Return the PDF for a completed review."""
    reviewed = review.completed_at.replace(tzinfo=timezone.utc).strftime("%d %b %Y %H:%M UTC") if review.completed_at else ""
    pdf = _Report(f"DocReview report - {review.document_title} v{review.version_number} - review #{review.id}")
    pdf.add_page()

    # ----- Header -----
    pdf.para("DocReview quality report", size=9, color=GREY)
    pdf.para(review.document_title, size=18, style="B", height=9)
    pdf.ln(2)
    pdf.label_value("Document type", review.document_type_name)
    pdf.label_value("Version", f"{review.version_number} ({review.original_filename})")
    if review.project_name:
        pdf.label_value("Project", review.project_name)
    pdf.label_value("Uploaded by", review.uploaded_by)
    pdf.label_value("Reviewed", reviewed)
    pdf.label_value("Rulebook", f"version {review.rulebook_version}, {review.rule_count} rules")
    pdf.label_value("Reviewer", f"{review.model_name} (prompt {review.prompt_version})")
    if review.is_demo:
        pdf.ln(2)
        pdf.para("DEMO REVIEW: these results come from keyword matching, not AI. Do not use them to judge the document.", size=9, style="B", color=AMBER)

    # ----- Score -----
    pdf.ln(4)
    pdf.rule_line()
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*DARK)
    pdf.cell(30, 14, str(review.score))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    pdf.cell(30, 14, "out of 100")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*(GREEN if review.passed else RED))
    pdf.cell(0, 14, "PASS" if review.passed else "FAIL", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.para(f"Pass mark: {review.pass_threshold}, and no critical rule may be Not Met.", size=9, color=GREY)
    if review.critical_failures:
        names = "; ".join(f"{r.rule_id} {r.title}" for r in review.critical_failures)
        pdf.ln(1)
        pdf.para(f"Critical rule failed: {names}. The document fails regardless of its score.", size=10, style="B", color=RED)
    if review.comparison:
        c = review.comparison
        sign = "+" if c.score_change >= 0 else ""
        pdf.ln(1)
        pdf.para(f"Change from version {c.previous_version_number}: {sign}{c.score_change} points (was {c.previous_score}).", size=10)
        if c.rules_updated:
            pdf.para("The rulebook changed between these versions.", size=9, color=AMBER)
        if c.newly_met:
            pdf.para("Now met: " + ", ".join(f"{r.rule_id} {r.title}" for r in c.newly_met), size=9)
        if c.newly_not_met:
            pdf.para("Now not met: " + ", ".join(f"{r.rule_id} {r.title}" for r in c.newly_not_met), size=9)

    # ----- Categories -----
    pdf.heading("Score by category")
    pdf.set_font("Helvetica", "", 10)
    for cat in review.categories:
        pdf.set_text_color(*DARK)
        pdf.cell(70, 6, _clean(cat.category))
        pdf.cell(0, 6, f"{_points(cat.points_earned)} / {cat.points_possible} points", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ----- Rules -----
    pdf.heading("Rule checklist")
    for rule in review.rules:
        status_color = {"met": GREEN, "partially_met": AMBER, "not_met": RED}[rule.status]
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK)
        title = f"{rule.rule_id}  {rule.title}" + ("  [critical]" if rule.critical else "")
        pdf.multi_cell(130, 5, _clean(title), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_text_color(*status_color)
        pdf.multi_cell(0, 5, f"{STATUS_LABELS[rule.status]}  ({_points(rule.points_earned)}/{rule.points_possible})", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.para(rule.explanation, size=9)
        pdf.para(f'Evidence: "{rule.evidence}" ({rule.location})', size=8, style="I", color=GREY)
        pdf.ln(1)
        pdf.rule_line()

    # ----- Suggestions -----
    for kind, label in SUGGESTION_SECTIONS:
        items = [(rule, s) for rule in review.rules for s in rule.suggestions if s.type == kind]
        pdf.heading(f"Suggestions: {label} ({len(items)})")
        if not items:
            pdf.para("None.", size=9, color=GREY)
            continue
        for rule, s in items:
            pdf.para(f"{rule.rule_id} {rule.title}  -  {s.location}  [{STATE_LABELS.get(s.user_state, s.user_state)}]", size=9, style="B")
            if s.current_text:
                pdf.para(("Remove: " if kind == "delete" else "Current: ") + s.current_text, size=9, color=GREY)
            if s.proposed_text:
                pdf.para(("Add: " if kind == "add" else "Replace with: ") + s.proposed_text, size=9)
            pdf.para(f"Why: {s.rationale}", size=8, style="I", color=GREY)
            pdf.ln(2)

    return bytes(pdf.output())

"""
Generate a PDF analysis of Type 4 argument grammar
across three TCS papers: Baća 2024, Finlayson 2021, Baier 2023.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import (
    HexColor, white, black, Color
)
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable

# ── Colour palette ───────────────────────────────────────────────────────────
DARK      = HexColor("#1a1a2e")
ACCENT    = HexColor("#e94560")
LIGHT_BG  = HexColor("#f4f4f8")
MID_GREY  = HexColor("#8a8a9a")
PALE_BLUE = HexColor("#e8eaf6")
PALE_RED  = HexColor("#fce4ec")
PALE_GRN  = HexColor("#e8f5e9")
BOX_BG    = HexColor("#f0f0f7")
RULE_COL  = HexColor("#c8c8d8")
MOVE_CLR  = {
    "puzzle_diagnosis":        HexColor("#5c6bc0"),
    "rival_mapping":           HexColor("#7e57c2"),
    "framework_proposal":      HexColor("#26a69a"),
    "case_introduction":       HexColor("#66bb6a"),
    "case_development":        HexColor("#9ccc65"),
    "case_interpretation":     HexColor("#ffa726"),
    "normative_derivation":    HexColor("#ef5350"),
    "genealogical_reconstruction": HexColor("#8d6e63"),
    "immanent_critique":       HexColor("#ab47bc"),
    "conclusion_open":         HexColor("#78909c"),
    "conceptual_distinction":  HexColor("#29b6f6"),
}
OPTIONAL  = HexColor("#bdbdbd")

# ── Page setup ───────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    s = getSampleStyleSheet()

    base = ParagraphStyle("base",
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=DARK, alignment=TA_JUSTIFY,
        spaceAfter=4)

    title_s = ParagraphStyle("title",
        fontName="Helvetica-Bold", fontSize=22, leading=28,
        textColor=DARK, spaceAfter=6, alignment=TA_LEFT)

    subtitle_s = ParagraphStyle("subtitle",
        fontName="Helvetica", fontSize=13, leading=18,
        textColor=MID_GREY, spaceAfter=18, alignment=TA_LEFT)

    section_s = ParagraphStyle("section",
        fontName="Helvetica-Bold", fontSize=14, leading=18,
        textColor=ACCENT, spaceAfter=6, spaceBefore=18)

    sub_s = ParagraphStyle("subsection",
        fontName="Helvetica-Bold", fontSize=11, leading=15,
        textColor=DARK, spaceAfter=4, spaceBefore=10)

    body_s = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9.5, leading=14.5,
        textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=6)

    cite_s = ParagraphStyle("cite",
        fontName="Helvetica-Oblique", fontSize=8.8, leading=13,
        textColor=MID_GREY, leftIndent=18, spaceAfter=4)

    label_s = ParagraphStyle("label",
        fontName="Helvetica-Bold", fontSize=8, leading=11,
        textColor=white, alignment=TA_CENTER)

    caption_s = ParagraphStyle("caption",
        fontName="Helvetica", fontSize=8.2, leading=12,
        textColor=MID_GREY, spaceAfter=10, alignment=TA_CENTER)

    box_s = ParagraphStyle("box",
        fontName="Helvetica", fontSize=9, leading=13.5,
        textColor=DARK, leftIndent=10, rightIndent=10,
        spaceAfter=4, alignment=TA_JUSTIFY)

    box_head_s = ParagraphStyle("box_head",
        fontName="Helvetica-Bold", fontSize=9.2, leading=13,
        textColor=DARK, leftIndent=10, spaceAfter=3)

    meta_s = ParagraphStyle("meta",
        fontName="Helvetica", fontSize=8.5, leading=13,
        textColor=MID_GREY, spaceAfter=2)

    return dict(
        base=base, title=title_s, subtitle=subtitle_s,
        section=section_s, sub=sub_s, body=body_s,
        cite=cite_s, label=label_s, caption=caption_s,
        box=box_s, box_head=box_head_s, meta=meta_s
    )


# ── Custom flowables ─────────────────────────────────────────────────────────

class MoveChain(Flowable):
    """Renders a horizontal move-sequence strip."""
    MOVES = [
        ("puzzle_diagnosis",            "PD"),
        ("rival_mapping",               "RM"),
        ("framework_proposal",          "FP"),
        ("case_introduction",           "CI"),
        ("case_development",            "CD"),
        ("case_interpretation",         "CIntp"),
        ("normative_derivation",        "ND"),
        ("conclusion_open",             "CO"),
    ]
    OPT = {"rival_mapping", "normative_derivation"}

    def __init__(self, active, width, optional_override=None):
        super().__init__()
        self.active = active
        self.width = width
        self.opt = optional_override if optional_override else self.OPT

    def wrap(self, aw, ah):
        return self.width, 28

    def draw(self):
        c = self.canv
        n = len(self.MOVES)
        box_w = (self.width - 6 * (n - 1)) / n
        x = 0
        for key, lbl in self.MOVES:
            is_active = key in self.active
            is_opt = key in self.opt
            fill = MOVE_CLR.get(key, HexColor("#999999")) if is_active else (
                HexColor("#e8e8f0") if not is_opt else HexColor("#f5f5f5"))
            txt_col = white if is_active else (RULE_COL if not is_opt else OPTIONAL)
            c.setFillColor(fill)
            c.setStrokeColor(RULE_COL if not is_active else fill)
            c.roundRect(x, 4, box_w, 20, 3, fill=1, stroke=1)
            c.setFillColor(txt_col)
            c.setFont("Helvetica-Bold" if is_active else "Helvetica", 6.5)
            c.drawCentredString(x + box_w / 2, 11.5, lbl)
            if is_opt and not is_active:
                c.setFont("Helvetica", 5)
                c.drawCentredString(x + box_w / 2, 5.5, "(opt)")
            x += box_w + 6


class ColourBar(Flowable):
    def __init__(self, color, width, height=4):
        super().__init__()
        self.color = color
        self.width = width
        self.height = height

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


def hr(style="solid"):
    return HRFlowable(
        width="100%", thickness=0.5,
        color=RULE_COL, spaceAfter=8, spaceBefore=4)


def coloured_box(paragraphs, bg=BOX_BG, left_bar_color=None):
    """Wrap content in a rounded-corner table cell."""
    if left_bar_color:
        data = [[Spacer(8, 1), [p for p in paragraphs]]]
        col_widths = [8, CONTENT_W - 8]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (0, -1), left_bar_color),
            ("BACKGROUND",   (1, 0), (1, -1), bg),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            # zero out all padding first, then set per-column
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
            ("LEFTPADDING",  (1, 0), (1, -1), 10),
            ("RIGHTPADDING", (1, 0), (1, -1), 10),
        ]))
    else:
        t = Table([[paragraphs]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), bg),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))
    return t


# ── Content ──────────────────────────────────────────────────────────────────

def build_document():
    ST = make_styles()
    story = []

    # ── Cover / header ───────────────────────────────────────────────────────
    story.append(ColourBar(DARK, CONTENT_W, 6))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Argument Grammar of Type 4", ST["title"]))
    story.append(Paragraph(
        "Diagnostic Framework via Contemporary Case", ST["subtitle"]))
    story.append(Paragraph(
        "Theory, Culture &amp; Society — close reading of three papers",
        ST["meta"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(hr())
    story.append(Spacer(1, 0.2 * cm))

    # ── Introduction ─────────────────────────────────────────────────────────
    story.append(Paragraph("Overview", ST["section"]))
    story.append(Paragraph(
        "This document analyses the shared argument grammar of three papers "
        "from <i>Theory, Culture &amp; Society</i> that exemplify <b>Type 4</b> "
        "in the TCS typology: the <i>diagnostic framework via contemporary case</i>. "
        "In Type 4, a theoretical framework imported from a recognised intellectual "
        "tradition is applied to a contemporary political or cultural phenomenon. "
        "The case generates refinements or corrections to the framework, but the "
        "conceptual architecture precedes the case. The conclusion is almost always "
        "open — the case reveals complexity rather than resolving it.",
        ST["body"]))
    story.append(Paragraph(
        "The three papers analysed are:", ST["body"]))

    papers = [
        ["Baća (2024)", "QAnon and the Epistemic Communities of the Unreal",
         "Jameson · White · Isin", "Normative/interpretive"],
        ["Finlayson (2021)", "Neoliberalism, the Alt-Right and the Intellectual Dark Web",
         "Freeden · Dardot/Laval · Burnham", "Ideological analysis"],
        ["Baier (2023)", "Narratives of Post-Truth: Lyotard and the Epistemic Fragmentation of Society",
         "Lyotard · Abbott · Koschorke", "Conceptual reconstruction"],
    ]
    tbl = Table(
        [["Paper", "Title", "Framework sources", "Mode"]] + papers,
        colWidths=[2.6 * cm, 6.0 * cm, 4.6 * cm, 3.4 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("LEADING",       (0, 0), (-1, -1), 12),
        ("BACKGROUND",    (0, 1), (-1, -1), LIGHT_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, LIGHT_BG]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, RULE_COL),
    ]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── Standard move sequence ───────────────────────────────────────────────
    story.append(Paragraph("The Standard Move Sequence", ST["section"]))
    story.append(Paragraph(
        "Type 4 papers follow a recognisable seven- or eight-move grammar. "
        "Two moves are optional (shown in grey): <b>rival_mapping</b> is "
        "present when the paper explicitly contests an inadequate prior approach; "
        "<b>normative_derivation</b> appears only when the paper draws an "
        "explicit prescriptive conclusion rather than a diagnostic one. "
        "The sequence below shows the canonical form.",
        ST["body"]))
    story.append(Spacer(1, 0.3 * cm))

    all_moves = [m[0] for m in MoveChain.MOVES]
    story.append(MoveChain(all_moves, CONTENT_W))
    story.append(Spacer(1, 0.15 * cm))

    move_labels = [
        ("PD", "puzzle_diagnosis",
         "Names a problem in existing accounts — usually an absence (no adequate "
         "sociology of conspiracism; no ideological analysis; no rigorous "
         "functional theory of post-truth)."),
        ("RM", "rival_mapping",
         "<i>[optional]</i> Surveys the inadequate responses. In Baća: the three "
         "pathologizing traditions. In Finlayson: inductive community-mapping studies. "
         "In Baier: prior Lyotard scholarship that ignores internal inconsistencies."),
        ("FP", "framework_proposal",
         "Introduces the theoretical vocabulary that will reframe the case: "
         "Baća's three non-pathologizing concepts; Finlayson's ideology-theory "
         "of the 'ideological family'; Baier's redefined <i>petit récit</i> "
         "and 'epistemic sphere'."),
        ("CI", "case_introduction",
         "Identifies the contemporary phenomenon that will test or extend the "
         "framework: QAnon (Baća); the alt-right/IDW ecosystem (Finlayson); "
         "Trump's MAGA movement (Baier)."),
        ("CD", "case_development",
         "Reconstructs the phenomenon in detail — not as raw description but "
         "through the categories already proposed. The framework gives the "
         "case its shape."),
        ("CIntp", "case_interpretation",
         "Draws out what the case reveals about the framework and the "
         "phenomenon — the moment of theoretical payoff. Baća: QAnon as "
         "performative citizenship. Finlayson: the online right as a critique "
         "of neoliberalism formed <i>within</i> neoliberalism. Baier: MAGA as "
         "a petit récit establishing an epistemic sphere."),
        ("ND", "normative_derivation",
         "<i>[optional]</i> States a normative or prescriptive conclusion. "
         "Absent or very implicit in all three papers — the diagnosis is the "
         "contribution; prescription is left to the reader."),
        ("CO", "conclusion_open",
         "Restates the framework's contribution and names the research agenda "
         "opened — not a resolution but a provocation to further work."),
    ]

    for short, key, desc in move_labels:
        color = MOVE_CLR.get(key, HexColor("#888888"))
        is_opt = key in MoveChain.OPT
        bg = PALE_BLUE if not is_opt else HexColor("#f9f9f9")
        row = Table(
            [[
                Paragraph(f"<b>{short}</b>", ST["label"]),
                [Paragraph(key.replace("_", " "), ST["box_head"]),
                 Paragraph(desc, ST["box"])]
            ]],
            colWidths=[1.4 * cm, CONTENT_W - 1.4 * cm])
        row.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), color if not is_opt else OPTIONAL),
            ("BACKGROUND",    (1, 0), (1, 0), bg),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (0, 0), 0),
            ("RIGHTPADDING",  (0, 0), (0, 0), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (1, 0), (1, 0), 10),
            ("LINEABOVE",     (0, 0), (-1, 0), 0.5, RULE_COL),
        ]))
        story.append(row)

    story.append(Spacer(1, 0.4 * cm))

    # ── Three-paper comparison table ─────────────────────────────────────────
    story.append(Paragraph("Cross-Paper Comparison", ST["section"]))
    story.append(Paragraph(
        "The table below maps each move to its realisation in each paper, "
        "showing how the same functional grammar produces three distinct arguments.",
        ST["body"]))
    story.append(Spacer(1, 0.25 * cm))

    cmp_data = [
        ["Move", "Baća 2024\n(QAnon)", "Finlayson 2021\n(Alt-right)", "Baier 2023\n(Post-truth)"],
        ["puzzle_diagnosis",
         "COVID/disinfodemic has\nmainstreamed conspiracism;\nexisting frameworks are\npathologizing and miss\nits political significance",
         "Data-driven platform\nstudies map communities\nbut cannot explain the\nshared ideological\narchitecture of the\nonline right",
         "Post-truth is everywhere\nbut lacks a rigorous\nfunctional theory;\nLyotard's petit récit\npromising but internally\ninconsistent"],
        ["rival_mapping",
         "Three stigmas:\npsychopathology,\npseudoscience,\nparapolitics — each\ndepoliticizes conspiracism",
         "Lewis's Alternative\nInfluence Network and\nMunger/Philips's taxonomy:\ndescribe communities\nbut miss ideological\ncoherence",
         "Prior Lyotard scholarship\n(Sim, McLennan) applies\nthe differend but ignores\nthe inconsistency of\n'narrative'; narratologists\nignore cultural narratives"],
        ["framework_proposal",
         "Three non-pathologizing\nconcepts: cognitive mapping\n(Jameson), narrative\nemplotment (White),\nperformative citizenship\n(Isin)",
         "Freeden's morphological\nideology theory + Dardot\n& Laval's 'ideological\nentrepreneurship' →\nthe 'ideological family'\nunited by anti-egalitarianism",
         "Step 1: redefine narrative\n(Abbott + Koschorke) →\ncultural narrative.\nStep 2: redefine petit récit\nas type of cultural\nnarrative. Step 3: derive\n'epistemic sphere'"],
        ["case_introduction",
         "QAnon: emerges 2017,\ncryptic Q-drops on 4chan,\nCapitol storming Jan 2021.\nSelected as most\nprominent right-wing\ndigital conspiracism",
         "Alt-right (Spencer/Radix),\nAlt-lite (Watson, Cernovich),\nIDW (Peterson, Murray),\npaleoconservatives (Francis,\nTaylor). Online ecosystem\nselected for its breadth\nand ideological diversity",
         "Trump's MAGA movement:\nMAGA slogan as micro-plot,\nTriadic myth (golden age →\ndisruption → restoration).\nSelected as paradigm\ncase of post-truth politics"],
        ["case_development",
         "QAnon as epistemic\ncommunity of the unreal:\nparticipatory, gamified,\ndecentralized. Q-drops\nas collaborative knowledge\nproduction. COVID\nas accelerant.",
         "Genealogical reconstruction:\nfrom Burnham's managerial\nrevolution through\nneoconservative 'new class'\n(Kristol, Gottfried) to\nonline anti-egalitarianism.\nRace-realism, sex-realism,\nneoreaction as variants.",
         "MAGA as petit récit:\nlocally limited counter-\nnarrative that establishes\nown epistemic criteria\n(tribal epistemology).\nFBI Mar-a-Lago raid as\ncase: reinforces epistemic\ndifferend from mainstream"],
        ["case_interpretation",
         "QAnon = performative\ncitizenship: political\nsubjectification,\ncosmological world-\nbuilding, collective\ndisalienation. Grassroots\nconsipiracism not pathology\nbut alternative political\npractice.",
         "Online right critiques\n'actually-existing' neo-\nliberalism yet insists on\nneoliberal rationality.\n'Red pill' as interpellation\ninto entrepreneurial self.\nThis is neoliberalism's\nown populist bastards —\ncritique formed within,\nnot against, the system.",
         "Post-truth = multiple\nepistemic spheres, each\nfounded on a petit récit,\nseparated by epistemic\ndifferends. Lyotard's\npaganism/archipelago\nrevised: spheres are\nincommensurable, not\njust in tension."],
        ["normative_derivation",
         "[absent — implicit:\npathologizing conspiracism\nis democratically costly]",
         "[absent — implicit:\nonline reactionary politics\nis not a post-neoliberal\nalternative but neoliberalism\ncontinued by other means]",
         "[absent — implicit:\nepistemic fragmentation\nthreatens the democratic\nepistemic contract]"],
        ["conclusion_open",
         "Non-pathologizing shift\nrequires studying counter-\nknowledge, counter-\nmovements as politics.\nResearch agenda: sociology\nof grassroots conspiracism.",
         "Understanding online right\nrequires both ideological\nhistory and platform\npolitical economy together.\nNeither alone is sufficient.",
         "Post-truth = epistemic\nfragmentation into spheres\nseparated by differends.\nThreat to democratic\nepistemic contract.\nResearch agenda open."],
    ]

    col_w = [3.2 * cm, 4.5 * cm, 4.5 * cm, 4.4 * cm]
    cmp_tbl = Table(cmp_data, colWidths=col_w, repeatRows=1)
    cmp_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("LEADING",       (0, 0), (-1, -1), 11),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, RULE_COL),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, LIGHT_BG]),
        ("BACKGROUND",    (0, 7), (-1, 7), PALE_RED),  # normative_derivation row
        ("TEXTCOLOR",     (0, 7), (0, 7), MID_GREY),
    ]))
    story.append(cmp_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── Individual paper analyses ────────────────────────────────────────────
    story.append(PageBreak())

    papers_full = [
        {
            "author": "Baća (2024)",
            "title": "QAnon and the Epistemic Communities of the Unreal: "
                     "A Conceptual Toolkit for a Sociology of Grassroots Conspiracism",
            "journal": "Theory, Culture & Society, 41(4): 111–132",
            "bar_color": MOVE_CLR["puzzle_diagnosis"],
            "active_moves": [
                "puzzle_diagnosis", "rival_mapping", "framework_proposal",
                "case_introduction", "case_interpretation",
                "case_interpretation", "case_interpretation", "conclusion_open"
            ],
            "framework": "Jameson (cognitive mapping), Hayden White (narrative emplotment), "
                         "Engin Isin (performative citizenship)",
            "case": "QAnon movement (2017–present), with reference to "
                    "COVID-19 disinfodemic and the January 2021 Capitol storming",
            "variant": "4a — Political movement as diagnostic occasion. "
                       "Toolkit-building variant: rather than applying a single "
                       "framework, the paper constructs a three-concept toolkit, "
                       "making the framework_proposal unusually elaborate.",
            "moves": [
                ("puzzle_diagnosis",
                 "Opening: From Pathologizing to Politicizing Conspiracy Theories",
                 "The paper opens with a double problem statement. "
                 "First, a contextual diagnosis: COVID and the disinfodemic have "
                 "mainstreamed conspiracism. Second, a scholarly gap: existing "
                 "frameworks (psychopathology, pseudoscience, parapolitics) all "
                 "pathologize conspiracism and thereby depoliticize it — they "
                 "cannot account for its genuine sociological significance as a "
                 "form of political meaning-making from below. The Giddens epigraph "
                 "('runaway world') frames this as a structural condition, not "
                 "individual pathology.",
                 '"The messy politics of combating the COVID-19 pandemic… led to '
                 'an unintended consequence – a perfect storm of populism, '
                 'pseudoscientism, and conspiracism within the public sphere." (p. 112)'),
                ("rival_mapping",
                 "Section: The Three Stigmas of Conspiracist Ideation",
                 "Baća maps three rival frameworks in parallel, treating each as "
                 "a distinct 'stigma'. (1) Psychopathological accounts diagnose "
                 "conspiracists as paranoid or schizotypal, detaching conspiracism "
                 "from social and political dynamics. (2) Pseudoscience framings "
                 "treat conspiracy theories as quasi-religious bad science — "
                 "'crippled epistemology'. (3) Parapolitical framings reduce "
                 "conspiracism to toxic anti-democratic behaviour. Each framework "
                 "is shown to share a common defect: it normalises the academic "
                 "standpoint as the criterion of political legitimacy.",
                 '"The proposed depathologization-through-politicization does not '
                 'indicate sympathy with conspiracists; instead, it involves the '
                 'theoretical reframing of conspiracism at the grassroots level… '
                 'as a means to develop a conceptual toolkit." (p. 117)'),
                ("framework_proposal",
                 "Section: Towards a Sociology of Grassroots Conspiracism",
                 "Three non-pathologizing conceptual counteroffers are introduced. "
                 "(1) Cognitive mapping (Jameson): conspiracism as an attempt to "
                 "map social totality when official maps have failed. (2) Narrative "
                 "emplotment (Hayden White): conspiracy theories as coherent "
                 "narrative structures giving meaning to dissonant events. "
                 "(3) Performative citizenship (Isin): conspiracist participation "
                 "as a form of citizenship claim — enacted, horizontal, and "
                 "bottom-up. Each concept is paired explicitly with one of the "
                 "three pathologizing stigmas it replaces.",
                 '"Rather than reducing conspiratorial thinking to an individual '
                 'mental issue, conspiracy theories to manipulative bad science, '
                 'and conspiracism to dangerous parapolitical behavior, this article '
                 'proposes non-pathologizing conceptual alternatives." (p. 125)'),
                ("case_introduction + case_interpretation ×3",
                 "Sections: Cognitive Mapping / Narrative Emplotment / Performative Citizenship through QAnon",
                 "QAnon is introduced as a 'case-in-point' — explicitly framed "
                 "as illustrative rather than constitutive. The paper then performs "
                 "three rounds of case_interpretation (one per concept): "
                 "(1) QAnon Q-drops as cognitive mapping of a conspiratorial totality. "
                 "(2) QAnon storytelling as narrative emplotment — "
                 "the movement as collaborative narrative game using 'retcon'. "
                 "(3) QAnon adherents as performative citizens undertaking "
                 "political subjectification through epistemic acts. The case "
                 "is read through each lens in sequence, not developed "
                 "independently of the framework.",
                 '"QAnon did not initially emerge as a cohesive conspiracy theory; '
                 'rather, it was articulated in the tradition of fanfiction or, '
                 'more accurately, enacted as an online narrative game." (p. 118)'),
                ("conclusion_open",
                 "Conclusion: Explanation before Condemnation?",
                 "The paper closes by naming two novel concepts produced "
                 "by the analysis — epistemic communities of the unreal and "
                 "grassroots conspiracism — and calling for a sociology that "
                 "studies these as politics rather than pathology. The conclusion "
                 "is explicitly programmatic (research agenda), not prescriptive. "
                 "The question mark in the title of the conclusion signals the "
                 "normative restraint: the paper diagnoses without prescribing.",
                 '"Not as pathologized individuals but as a politicized collective '
                 '– a conspiracist (counter)movement." (p. 724)'),
            ],
            "key_move": "The triple case_interpretation structure (one per concept) is unusual "
                        "and signals the toolkit-building variant: the paper is more concerned "
                        "with demonstrating the analytical productivity of each concept than "
                        "with building a continuous argument about QAnon.",
        },
        {
            "author": "Finlayson (2021)",
            "title": "Neoliberalism, the Alt-Right and the Intellectual Dark Web",
            "journal": "Theory, Culture & Society, 38(6): 167–190",
            "bar_color": MOVE_CLR["framework_proposal"],
            "active_moves": [
                "puzzle_diagnosis", "rival_mapping", "framework_proposal",
                "genealogical_reconstruction", "case_development",
                "case_interpretation", "conclusion_open"
            ],
            "framework": "Freeden's morphological ideology theory, Dardot & Laval's "
                         "'ideological entrepreneurship', Burnham/Kristol/Gottfried genealogy "
                         "of the 'new class' concept",
            "case": "The alt-right, alt-lite and Intellectual Dark Web online ecosystem: "
                    "American Renaissance, VDare, Radix Journal, Stefan Molyneux, "
                    "Jordan Peterson, Paul Joseph Watson, neoreaction",
            "variant": "4a — Political movement as diagnostic occasion. "
                       "Genealogical variant: the framework_proposal is embedded in "
                       "a genealogical_reconstruction of how anti-egalitarian ideas "
                       "travelled from paleoconservatism into online spaces.",
            "moves": [
                ("puzzle_diagnosis",
                 "Introduction: The Ideological Entrepreneur in the Digital Age",
                 "The paper opens by noting that digital platforms have "
                 "transformed 'ideological entrepreneurship' — the concept "
                 "from Dardot and Laval about writers and academics who "
                 "struggle against progressivism. Existing studies (Lewis's "
                 "Alternative Influence Network; Munger and Philips's taxonomy) "
                 "identify communities but cannot explain ideological coherence. "
                 "The stated goal is to complement data-driven approaches with "
                 "ideological-historical analysis.",
                 '"This article brings together and applies approaches from digital '
                 'media studies, political theory and rhetoric in order to understand '
                 'this phenomenon better." (p. 168)'),
                ("rival_mapping",
                 "Section: Right Online — Mapping the Field",
                 "Finlayson surveys Lewis's Alternative Influence Network study "
                 "and Munger and Philips's five-part community taxonomy. These "
                 "are acknowledged as useful descriptions that 'organise a large "
                 "field and distinguish some of its parts', but they 'paint only "
                 "a part of the picture'. The critique is an absence critique: "
                 "these accounts cannot explain why communities that ideologically "
                 "differ converge on shared anti-egalitarian hostility.",
                 '"Such analyses paint only a part of the picture and can be '
                 'complemented by research drawing on the history and development '
                 'of political ideas and ideologies." (p. 169)'),
                ("framework_proposal",
                 "Section: Ideologies Online — The Ideological Family",
                 "Freeden's morphological theory of ideology is introduced: "
                 "ideologies as fluid 'ideological families' whose core and "
                 "peripheral concepts shift under digital conditions. Digital "
                 "media erode ideological boundaries, creating new assemblages "
                 "where contradictory positions converge aesthetically and "
                 "affectively. The 'ideological family' of the online right is "
                 "proposed as the unit of analysis — held together not by doctrine "
                 "but by shared hostility to 'liberalism' understood as the denial "
                 "of natural inequality.",
                 '"What might have seemed historically, culturally and rationally '
                 'distinct is bound by the force and fire of algorithmic, affective '
                 'and aesthetic congruence." (p. 174)'),
                ("genealogical_reconstruction",
                 "Section: The 'New Class' — Intellectual Genealogy",
                 "This is Finlayson's most distinctive move: a genealogical "
                 "reconstruction tracing the 'new class' concept from Burnham's "
                 "managerial revolution (1941), through Kristol's neoconservative "
                 "critique of liberal intellectuals (1970s), through Gottfried's "
                 "paleoconservative version (1990s), and into European New Right "
                 "metapolitics (de Benoist). The online right's figuration of "
                 "'Social Justice Warriors' and 'Cultural Marxists' is shown to "
                 "be the latest instantiation of this longstanding anti-intelligentsia "
                 "discourse.",
                 "\u201cCentral to the articulation of this hostility is a concept of "
                 "the \u2018new class\u2019, which I place within a longstanding political "
                 "and critical literature.\u201d (p. 168)"),
                ("case_development + case_interpretation",
                 "Sections: The Red Pill / Entrepreneurial Selves",
                 "The case development moves through specific online actors "
                 "(Spencer, Molyneux, Watson, Peterson, Cernovich) to show "
                 "how anti-egalitarianism is expressed across the ideological "
                 "spectrum. The case_interpretation delivers the paper's core "
                 "finding: the 'red pill' is not a rejection of neoliberalism "
                 "but an interpellation into its entrepreneurial logic. "
                 "The online right offers critique of 'actually-existing' "
                 "neoliberalism while insisting on the 'rationality' of market "
                 "governance — a 'critique formed within rather than against' "
                 "neoliberalism (quoting Slobodian).",
                 '"To take the red pill is to accept such an interpellation '
                 'without reservation; to see that behind the mystifications '
                 'of the SJWs and Cultural Marxists, reality is a power struggle '
                 'between unequals." (p. 181)'),
                ("conclusion_open",
                 "Conclusion",
                 "Understanding online right politics requires both ideological "
                 "history and attention to the political economy of platforms — "
                 "neither alone is sufficient. The conclusion names the key "
                 "interpretive finding without prescribing a response: this is "
                 "a 'critique of new class verbalism formed within that class "
                 "and not against it'. The final sentence withholds normative "
                 "closure deliberately.",
                 '"For all that it appears as a restorationist critique of '
                 'third-way neoliberalism, this contemporary configuration of '
                 'reactionary politics is very much in tune… with the rhythms '
                 'and styles of what Byun-Hul Chan calls the \'achievement '
                 'society\'." (p. 182)'),
            ],
            "key_move": "The genealogical_reconstruction is the move that makes Finlayson's "
                        "version of Type 4 distinctive. Rather than simply applying Freeden's "
                        "framework to the contemporary case, the paper first traces how the key "
                        "concepts (new class, anti-egalitarianism) migrated from post-war "
                        "conservatism into online spaces — making the genealogy part of the "
                        "framework rather than part of the case.",
        },
        {
            "author": "Baier (2023)",
            "title": "Narratives of Post-Truth: Lyotard and the Epistemic "
                     "Fragmentation of Society",
            "journal": "Theory, Culture & Society, 41(1): 95–110",
            "bar_color": MOVE_CLR["conceptual_distinction"],
            "active_moves": [
                "puzzle_diagnosis", "framework_proposal", "immanent_critique",
                "conceptual_distinction", "framework_proposal",
                "case_introduction", "case_interpretation", "conclusion_open"
            ],
            "framework": "Lyotard (petit récit, The Differend, paganism/differend), "
                         "narratology (Genette, Abbott/masterplot, Koschorke), "
                         "Wittgenstein (language games — recruited critically)",
            "case": "Donald Trump's MAGA movement; illustrative reference to Brexit, "
                    "Covid deniers, climate change deniers",
            "variant": "4a — Political movement as diagnostic occasion. "
                       "Conceptual reconstruction variant: the framework is not "
                       "ready-made but must be built in two steps (cultural narrative "
                       "→ redefined petit récit → epistemic sphere) before it can "
                       "reach the case. This gives the paper an unusually elaborate "
                       "framework_proposal section.",
            "moves": [
                ("puzzle_diagnosis",
                 "Introduction",
                 "Post-truth dominates public discourse but lacks a rigorous "
                 "functional theory. Lyotard's concept of petit récit is "
                 "structurally similar to the post-truth phenomenon — both "
                 "involve small counter-narratives resisting hegemonic discourse — "
                 "but Lyotard uses 'narrative' inconsistently (as phrase regimen, "
                 "discursive genre, and something else), making the concept "
                 "analytically unusable without reconstruction. The paper promises "
                 "to fix the inconsistency and put the concept to work.",
                 '"Due to these inconsistencies, the concept can hardly be '
                 'considered a well-defined category, making it difficult to '
                 'apply to a phenomenon like post-truth." (p. 96)'),
                ("framework_proposal [step 1] + immanent_critique",
                 "Section: Lyotard on Narrative",
                 "The paper opens the framework by surveying Lyotard's own "
                 "account. This is immediately followed by an immanent critique: "
                 "Lyotard conflates narrative (a phrase regimen) with language "
                 "games (also a phrase regimen), treating them as functionally "
                 "equivalent, which they are not. Wittgenstein is recruited to "
                 "show why language games and narratives are structurally "
                 "different. The result: Lyotard's concept cannot be applied "
                 "to post-truth without prior reconstruction.",
                 '"While narratives and language games might be functionally '
                 'equivalent within Lyotard\'s phrase linguistics, the two '
                 'entities are fundamentally different by any external '
                 'standard." (p. 183)'),
                ("conceptual_distinction + framework_proposal [step 2]",
                 "Section: From Textual to Cultural Narrative",
                 "The reconstruction proceeds in two steps. First, a conceptual "
                 "distinction between textual and cultural narrative: borrowing "
                 "Abbott's 'masterplot' and Koschorke's 'narrative pattern', "
                 "Baier defines cultural narrative as 'a discursive constellation "
                 "connecting the multitudes of narrative discourses circulating "
                 "within a community to a smaller number of abstract narrative "
                 "patterns'. Second, the newly defined cultural narrative is "
                 "used to redefine Lyotard's petit récit as a particular type "
                 "of cultural narrative — locally and temporally limited, "
                 "functioning as counter-narrative. From this, the concept of "
                 "'epistemic sphere' is derived: each petit récit establishes "
                 "its own criteria for truth.",
                 '"A cultural narrative is a discursive constellation connecting '
                 'the multitudes of narrative discourses circulating within a '
                 'community to a smaller number of abstract narrative patterns '
                 'or masterplots." (p. 354)'),
                ("case_introduction",
                 "Section: Post-Truth and Populism",
                 "Trump's MAGA movement is introduced as 'the most prominent "
                 "example of post-truth politics'. The introduction includes a "
                 "brief contextualisation within contemporary populism more "
                 "broadly (Boris Johnson, AfD, PiS, Fidesz) — Baier signals "
                 "that the MAGA case is not idiosyncratic but paradigmatic.",
                 "\u201cDonald Trump presents himself as fighting for the interests "
                 "of supposedly \u2018ordinary Americans\u2019 against intellectual elites "
                 "and the political establishment.\u201d (p. 104)"),
                ("case_interpretation",
                 "Section: Applying the Framework to MAGA",
                 "The MAGA slogan is read as a 'microplot' in Koschorke's sense: "
                 "the triadic sequence of golden age → disruption → restoration "
                 "by a hero. This functions as a petit récit: it is locally "
                 "limited, counter-hegemonic within a populist logic of "
                 "'rigged' system, and establishes its own epistemic sphere "
                 "(tribal epistemology). The FBI Mar-a-Lago raid is interpreted "
                 "as an event that reinforces the epistemic differend — from "
                 "within the MAGA sphere, it confirms the conspiratorial "
                 "narrative of a weaponised state.",
                 '"MAGA invokes a narrative pattern familiar from ancient myths '
                 'and modern blockbuster movies alike: the triadic sequence of '
                 'an original state of harmony, its disruption and eventual '
                 'utopian restitution through the efforts of a hero." (p. 105)'),
                ("conclusion_open",
                 "Conclusion",
                 "The post-truth environment consists of multiple epistemic "
                 "spheres separated by epistemic differends — inhabitants do "
                 "not just disagree about facts but about what truth is. "
                 "This undermines 'the epistemic contract' that democracy "
                 "requires. The conclusion names this as a threat without "
                 "prescribing a cure. The normative charge is implicit: the "
                 "diagnosis is the contribution.",
                 '"By undermining the epistemic contract, post-truth poses a '
                 'threat to democratic societies all over the world." (p. 106)'),
            ],
            "key_move": "The double framework_proposal (interrupted by immanent_critique and "
                        "conceptual_distinction) is Baier's most distinctive structural feature. "
                        "The paper cannot proceed to the case until the framework is rebuilt "
                        "from within — making the framework_proposal section occupy roughly "
                        "two-thirds of the article.",
        },
    ]

    for p in papers_full:
        story.append(Paragraph(p["author"], ST["section"]))
        story.append(Paragraph(p["title"], ST["sub"]))
        story.append(Paragraph(p["journal"], ST["meta"]))
        story.append(Spacer(1, 0.2 * cm))

        # Meta box
        meta_rows = [
            ["Framework sources", p["framework"]],
            ["Case", p["case"]],
            ["Type 4 variant", p["variant"]],
        ]
        meta_tbl = Table(meta_rows, colWidths=[3.6 * cm, CONTENT_W - 3.6 * cm])
        meta_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (0, -1), PALE_BLUE),
            ("BACKGROUND",   (1, 0), (1, -1), BOX_BG),
            ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("LEADING",      (0, 0), (-1, -1), 12),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LINEBELOW",    (0, 0), (-1, -2), 0.4, RULE_COL),
        ]))
        story.append(meta_tbl)
        story.append(Spacer(1, 0.3 * cm))

        # Move chain for this paper
        story.append(MoveChain(p["active_moves"], CONTENT_W))
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph("Active moves shown. Grey = optional/absent.", ST["caption"]))
        story.append(Spacer(1, 0.3 * cm))

        # Move-by-move analysis
        story.append(Paragraph("Move-by-move analysis", ST["sub"]))
        for move_key, section_title, analysis, quote in p["moves"]:
            color = MOVE_CLR.get(move_key.split("+")[0].strip().split(" ")[0], HexColor("#888888"))
            short = move_key.split("_")[0][:2].upper() if "_" in move_key else move_key[:4].upper()

            content = [
                Paragraph(f"<b>{move_key}</b>", ST["box_head"]),
                Paragraph(f"<i>{section_title}</i>", ST["box"]),
                Paragraph(analysis, ST["box"]),
                Spacer(1, 4),
                Paragraph(f'"{quote}"', ST["cite"]),
            ]
            row = Table([[content]], colWidths=[CONTENT_W])
            row.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BG),
                ("LINEBEFORE",   (0, 0), (0, -1), 3, color),
                ("LEFTPADDING",  (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING",   (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
            ]))
            story.append(KeepTogether(row))
            story.append(Spacer(1, 0.18 * cm))

        # Key move note
        story.append(coloured_box(
            [Paragraph("<b>Structural signature of this paper</b>", ST["box_head"]),
             Paragraph(p["key_move"], ST["box"])],
            bg=PALE_GRN, left_bar_color=MOVE_CLR["case_interpretation"]
        ))
        story.append(Spacer(1, 0.5 * cm))
        story.append(hr())
        story.append(PageBreak())

    # ── Comparative analysis ──────────────────────────────────────────────────
    story.append(Paragraph("What the Three Papers Share", ST["section"]))
    story.append(Paragraph(
        "Taken together, Baća, Finlayson, and Baier illustrate three routes "
        "into the same Type 4 grammar. The shared structure consists of four "
        "invariant features:", ST["body"]))

    features = [
        ("1. Framework precedes case",
         "In all three papers, the theoretical vocabulary is established — or "
         "rebuilt — before the contemporary case is introduced. The case does "
         "not generate the framework; it tests and extends it. This is the "
         "defining difference between Type 4 and Type 1 (where the case "
         "is constitutive of the argument)."),
        ("2. The contemporary case as diagnostic occasion",
         "QAnon, the alt-right ecosystem, and the MAGA movement are all treated "
         "as occasions for theoretical demonstration rather than primary objects "
         "of empirical study. The papers do not conduct fieldwork, interviews, "
         "or systematic content analysis of these phenomena. They read them "
         "interpretively through a pre-formed conceptual lens."),
        ("3. Normative restraint — diagnosis not prescription",
         "All three papers withhold explicit normative conclusions. The "
         "normative stakes are present (pathologizing conspiracism is "
         "democratically costly; online reactionary politics is not "
         "emancipatory; epistemic fragmentation threatens democracy) but "
         "they are stated as diagnoses, not prescriptions. This is why "
         "all three conclude with open conclusions and research agendas "
         "rather than political imperatives."),
        ("4. The framework is modified by the case",
         "None of the three papers simply applies a framework. Baća "
         "introduces two new concepts (epistemic communities of the unreal; "
         "grassroots conspiracism) that go beyond his three source concepts. "
         "Finlayson finds that the genealogical reconstruction reveals the "
         "online right's anti-neoliberal rhetoric as ultimately internal to "
         "neoliberalism — a finding that revises rather than confirms the "
         "simple 'post-neoliberal' diagnosis. Baier derives the concept of "
         "'epistemic differend' from applying Lyotard to MAGA — a concept "
         "not in Lyotard himself."),
    ]

    for title, body in features:
        story.append(coloured_box(
            [Paragraph(f"<b>{title}</b>", ST["box_head"]),
             Paragraph(body, ST["box"])],
            bg=BOX_BG, left_bar_color=ACCENT))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("The Three Variants Within Type 4", ST["section"]))
    story.append(Paragraph(
        "Each paper also exhibits a distinctive internal variation that "
        "marks it as a sub-type of the shared grammar:", ST["body"]))
    story.append(Spacer(1, 0.1 * cm))

    variant_data = [
        ["Paper", "Variant", "Structural signature", "Move where it shows"],
        ["Baća (2024)",
         "Toolkit-building",
         "The framework_proposal introduces three parallel concepts; "
         "case_interpretation is performed three times, once per concept",
         "framework_proposal (elaborate) + triple case_interpretation"],
        ["Finlayson (2021)",
         "Genealogical",
         "The genealogical_reconstruction is inserted between framework_proposal "
         "and case_development, showing how the key concepts migrated historically "
         "before they can be applied to the contemporary case",
         "genealogical_reconstruction (extra move)"],
        ["Baier (2023)",
         "Conceptual reconstruction",
         "The framework must be built before it can be applied: "
         "immanent_critique of Lyotard → conceptual_distinction → "
         "second framework_proposal",
         "double framework_proposal + immanent_critique + conceptual_distinction"],
    ]

    var_tbl = Table(variant_data, colWidths=[2.5 * cm, 2.5 * cm, 6.8 * cm, 4.8 * cm])
    var_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("LEADING",       (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, RULE_COL),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, LIGHT_BG]),
    ]))
    story.append(var_tbl)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Boundary with Adjacent Types", ST["section"]))
    boundaries = [
        ("Type 4 vs. Type 1 (Thick normative case)",
         "In Type 1, the case is constitutive: it generates new theoretical "
         "content that the framework alone could not produce. In all three "
         "Type 4 papers, the case illustrates and extends a framework that "
         "is already theoretically complete before the case is introduced. "
         "The test: could the framework_proposal section stand as an "
         "independent theoretical contribution without the contemporary case? "
         "In all three papers, the answer is yes — with Baier the closest "
         "to the boundary because his epistemic sphere concept is not fully "
         "derivable without the MAGA example."),
        ("Type 4 vs. Type 5 (Normative argument with empirical diagnosis)",
         "Type 5 papers conduct original empirical research — fieldwork, "
         "systematic discourse analysis, archival investigation. All three "
         "Type 4 papers read their cases interpretively using publicly "
         "available materials (Q-drops, YouTube channels, news rhetoric) "
         "without a method section or claim to systematic coverage. The "
         "test: does the paper have a method_justification move? None of "
         "these three papers does."),
    ]
    for title, body in boundaries:
        story.append(coloured_box(
            [Paragraph(f"<b>{title}</b>", ST["box_head"]),
             Paragraph(body, ST["box"])],
            bg=PALE_RED, left_bar_color=MID_GREY))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.5 * cm))
    story.append(ColourBar(DARK, CONTENT_W, 3))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Argument Grammar Analysis · Theory, Culture &amp; Society Corpus · Type 4",
        ST["caption"]))

    return story


# ── Output ───────────────────────────────────────────────────────────────────
OUT = "outputs/type4_argument_grammar.pdf"

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 1.2 * cm, "Type 4 Argument Grammar — TCS Corpus")
    canvas.drawRightString(PAGE_W - MARGIN, 1.2 * cm, f"p. {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    OUT,
    pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=2 * cm, bottomMargin=2 * cm,
    title="Type 4 Argument Grammar — TCS Corpus",
    author="Corpus Analysis"
)

story = build_document()
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF written to: {OUT}")

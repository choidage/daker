# -*- coding: utf-8 -*-
"""
바이브코딩 개선 아이디어 - PDF 생성 스크립트
현대적이고 심플한 디자인
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus import FrameBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Register Korean fonts (Malgun Gothic)
FONT_PATH = 'C:/Windows/Fonts/'
pdfmetrics.registerFont(TTFont('MalgunGothic', FONT_PATH + 'malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunGothicBold', FONT_PATH + 'malgunbd.ttf'))
pdfmetrics.registerFont(TTFont('MalgunGothicLight', FONT_PATH + 'malgunsl.ttf'))

# Map font family
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('MalgunGothic',
    normal='MalgunGothic',
    bold='MalgunGothicBold',
    italic='MalgunGothicLight',
    boldItalic='MalgunGothicBold'
)

# Define Korean-safe font names
FONT_REGULAR = 'MalgunGothic'
FONT_BOLD = 'MalgunGothicBold'
FONT_LIGHT = 'MalgunGothicLight'

# === Color Palette (Modern Dark Teal Theme) ===
DARK_BG = HexColor('#0F1419')
DARK_CARD = HexColor('#1A2332')
DARK_CARD_ALT = HexColor('#1E2A3A')
TEAL = HexColor('#0D6E6E')
TEAL_LIGHT = HexColor('#14918C')
ORANGE = HexColor('#E07B54')
TEXT_PRIMARY = HexColor('#1A1A1A')
TEXT_SECONDARY = HexColor('#444444')
TEXT_TERTIARY = HexColor('#666666')
TEXT_LIGHT = HexColor('#888888')
BG_WHITE = HexColor('#FFFFFF')
BG_LIGHT = HexColor('#F8FAFB')
BG_SECTION = HexColor('#F0F4F5')
BORDER_LIGHT = HexColor('#E0E6EA')
ACCENT_BLUE = HexColor('#2563EB')

# === Page Setup ===
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 25*mm
RIGHT_MARGIN = 25*mm
TOP_MARGIN = 20*mm
BOTTOM_MARGIN = 25*mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


def create_styles():
    styles = getSampleStyleSheet()

    # Cover title
    styles.add(ParagraphStyle(
        'CoverTitle',
        fontName=FONT_BOLD,
        fontSize=32,
        leading=40,
        textColor=TEAL,
        alignment=TA_LEFT,
        spaceAfter=8*mm,
    ))

    # Cover subtitle
    styles.add(ParagraphStyle(
        'CoverSubtitle',
        fontName=FONT_REGULAR,
        fontSize=14,
        leading=20,
        textColor=TEXT_SECONDARY,
        alignment=TA_LEFT,
        spaceAfter=4*mm,
    ))

    # Cover info
    styles.add(ParagraphStyle(
        'CoverInfo',
        fontName=FONT_REGULAR,
        fontSize=11,
        leading=18,
        textColor=TEXT_TERTIARY,
        alignment=TA_LEFT,
    ))

    # Section number
    styles.add(ParagraphStyle(
        'SectionNumber',
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=TEAL,
        spaceBefore=0,
        spaceAfter=2*mm,
        tracking=2,
    ))

    # Heading 1
    styles.add(ParagraphStyle(
        'H1',
        fontName=FONT_BOLD,
        fontSize=22,
        leading=28,
        textColor=TEXT_PRIMARY,
        spaceBefore=10*mm,
        spaceAfter=6*mm,
    ))

    # Heading 2
    styles.add(ParagraphStyle(
        'H2',
        fontName=FONT_BOLD,
        fontSize=16,
        leading=22,
        textColor=TEXT_PRIMARY,
        spaceBefore=8*mm,
        spaceAfter=4*mm,
    ))

    # Heading 3
    styles.add(ParagraphStyle(
        'H3',
        fontName=FONT_BOLD,
        fontSize=13,
        leading=18,
        textColor=TEAL,
        spaceBefore=5*mm,
        spaceAfter=3*mm,
    ))

    # Body text
    styles.add(ParagraphStyle(
        'BodyText2',
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=16,
        textColor=TEXT_SECONDARY,
        alignment=TA_JUSTIFY,
        spaceAfter=3*mm,
    ))

    # Quote / highlight
    styles.add(ParagraphStyle(
        'Quote',
        fontName=FONT_LIGHT,
        fontSize=11,
        leading=17,
        textColor=TEAL,
        alignment=TA_LEFT,
        leftIndent=10*mm,
        spaceBefore=4*mm,
        spaceAfter=4*mm,
        borderPadding=(3*mm, 5*mm, 3*mm, 5*mm),
    ))

    # Table header
    styles.add(ParagraphStyle(
        'TableHeader',
        fontName=FONT_BOLD,
        fontSize=9,
        leading=12,
        textColor=white,
        alignment=TA_CENTER,
    ))

    # Table cell
    styles.add(ParagraphStyle(
        'TableCell',
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=TEXT_SECONDARY,
        alignment=TA_CENTER,
    ))

    # Table cell left
    styles.add(ParagraphStyle(
        'TableCellLeft',
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=TEXT_SECONDARY,
        alignment=TA_LEFT,
    ))

    # Small caption
    styles.add(ParagraphStyle(
        'Caption',
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
        spaceAfter=2*mm,
    ))

    # Bullet item
    styles.add(ParagraphStyle(
        'BulletCustom',
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=15,
        textColor=TEXT_SECONDARY,
        leftIndent=8*mm,
        bulletIndent=3*mm,
        spaceAfter=1.5*mm,
    ))

    # Code block
    styles.add(ParagraphStyle(
        'CodeBlock',
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11,
        textColor=TEXT_PRIMARY,
        backColor=BG_SECTION,
        leftIndent=5*mm,
        rightIndent=5*mm,
        spaceBefore=2*mm,
        spaceAfter=2*mm,
        borderPadding=(3*mm, 3*mm, 3*mm, 3*mm),
    ))

    # Footer
    styles.add(ParagraphStyle(
        'Footer',
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
    ))

    return styles


class ProposalDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.page_count = 0

        # Cover page template
        cover_frame = Frame(
            LEFT_MARGIN, BOTTOM_MARGIN,
            CONTENT_WIDTH, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
            id='cover'
        )
        cover_template = PageTemplate(
            id='Cover',
            frames=[cover_frame],
            onPage=self._cover_page_bg
        )

        # Content page template
        content_frame = Frame(
            LEFT_MARGIN, BOTTOM_MARGIN + 8*mm,
            CONTENT_WIDTH, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN - 12*mm,
            id='content'
        )
        content_template = PageTemplate(
            id='Content',
            frames=[content_frame],
            onPage=self._content_page_bg
        )

        self.addPageTemplates([cover_template, content_template])

    def _cover_page_bg(self, canvas_obj, doc):
        canvas_obj.saveState()

        # White background
        canvas_obj.setFillColor(BG_WHITE)
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

        # Teal accent bar at top
        canvas_obj.setFillColor(TEAL)
        canvas_obj.rect(0, PAGE_HEIGHT - 8*mm, PAGE_WIDTH, 8*mm, fill=1, stroke=0)

        # Teal accent bar at left
        canvas_obj.setFillColor(TEAL)
        canvas_obj.rect(0, 0, 4*mm, PAGE_HEIGHT - 8*mm, fill=1, stroke=0)

        # Geometric decoration - bottom right
        canvas_obj.setFillColor(BG_SECTION)
        canvas_obj.rect(PAGE_WIDTH - 80*mm, 0, 80*mm, 60*mm, fill=1, stroke=0)

        canvas_obj.setFillColor(TEAL_LIGHT)
        canvas_obj.setFillAlpha(0.15)
        canvas_obj.rect(PAGE_WIDTH - 60*mm, 0, 60*mm, 40*mm, fill=1, stroke=0)

        canvas_obj.restoreState()

    def _content_page_bg(self, canvas_obj, doc):
        canvas_obj.saveState()

        # White bg
        canvas_obj.setFillColor(BG_WHITE)
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

        # Top accent line
        canvas_obj.setFillColor(TEAL)
        canvas_obj.rect(0, PAGE_HEIGHT - 2*mm, PAGE_WIDTH, 2*mm, fill=1, stroke=0)

        # Footer line
        canvas_obj.setStrokeColor(BORDER_LIGHT)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(LEFT_MARGIN, BOTTOM_MARGIN + 4*mm, PAGE_WIDTH - RIGHT_MARGIN, BOTTOM_MARGIN + 4*mm)

        # Page number
        canvas_obj.setFont(FONT_REGULAR, 8)
        canvas_obj.setFillColor(TEXT_LIGHT)
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, BOTTOM_MARGIN - 2*mm, f"- {page_num} -")

        # Header text
        canvas_obj.setFont(FONT_REGULAR, 7)
        canvas_obj.setFillColor(TEXT_LIGHT)
        canvas_obj.drawString(LEFT_MARGIN, PAGE_HEIGHT - 8*mm, "VIBE-X | Agent + MCP + RAG + Collaboration")
        canvas_obj.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 8*mm, "Team Vibe Emperor")

        canvas_obj.restoreState()


def make_table(data, col_widths=None, has_header=True):
    """Create a styled table."""
    style_commands = [
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_SECONDARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4*mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
    ]

    if has_header:
        style_commands.extend([
            ('BACKGROUND', (0, 0), (-1, 0), TEAL),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
        ])

    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_commands.append(('BACKGROUND', (0, i), (-1, i), BG_LIGHT))

    table = Table(data, colWidths=col_widths, repeatRows=1 if has_header else 0)
    table.setStyle(TableStyle(style_commands))
    return table


def make_highlight_box(text, styles):
    """Create a highlighted quote box."""
    box_data = [[Paragraph(text, styles['Quote'])]]
    box_table = Table(box_data, colWidths=[CONTENT_WIDTH - 5*mm])
    box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F0F8F8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 5*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 4*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4*mm),
        ('LINEBEFORECOL', (0, 0), (0, -1), 3, TEAL),
        ('ROUNDEDCORNERS', [0, 4, 4, 0]),
    ]))
    return box_table


def make_code_box(text, styles):
    """Create a code block."""
    box_data = [[Paragraph(text.replace('\n', '<br/>'), styles['CodeBlock'])]]
    box_table = Table(box_data, colWidths=[CONTENT_WIDTH - 5*mm])
    box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_SECTION),
        ('LEFTPADDING', (0, 0), (-1, -1), 5*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
        ('ROUNDEDCORNERS', [3, 3, 3, 3]),
    ]))
    return box_table


def make_metric_card(value, label, color=TEAL):
    """Create a metric card."""
    card_data = [
        [Paragraph(f'<font size="18" color="{color.hexval()}">{value}</font>', 
                    ParagraphStyle('mc', alignment=TA_CENTER, fontName=FONT_BOLD, fontSize=18, leading=24))],
        [Paragraph(f'<font size="8" color="{TEXT_LIGHT.hexval()}">{label}</font>', 
                    ParagraphStyle('mcl', alignment=TA_CENTER, fontName=FONT_REGULAR, fontSize=8, leading=11))]
    ]
    card_table = Table(card_data, colWidths=[35*mm])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (0, 0), 4*mm),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 4*mm),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('LINEBELOW', (0, 0), (-1, 0), 0, BG_LIGHT),
    ]))
    return card_table


def build_document():
    styles = create_styles()

    output_path = os.path.join(os.path.dirname(__file__), 'VibeCoding_Improvement_Proposal.pdf')

    doc = ProposalDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title='Vibe Coding Improvement Proposal',
        author='Team Vibe Emperor',
    )

    story = []

    # ===============================================
    # COVER PAGE
    # ===============================================
    story.append(Spacer(1, 40*mm))

    # Tag line
    story.append(Paragraph(
        '<font color="#0D6E6E" size="10">PROPOSAL  |  2026. 02. 11</font>',
        styles['CoverInfo']
    ))
    story.append(Spacer(1, 5*mm))

    # Title
    story.append(Paragraph(
        '바이브코딩<br/>개선 아이디어',
        styles['CoverTitle']
    ))

    # Subtitle
    story.append(Paragraph(
        'Agent + MCP + RAG + Collaboration 통합을 통한<br/>'
        '바이브 코딩의 구조적 한계 극복 전략',
        styles['CoverSubtitle']
    ))

    story.append(Spacer(1, 8*mm))

    # Divider
    story.append(HRFlowable(width="40%", thickness=2, color=TEAL, spaceAfter=8*mm, hAlign='LEFT'))

    # Info
    story.append(Paragraph(
        '<b>제안자</b>  :  팀 바이브제왕',
        styles['CoverInfo']
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<b>작성일</b>  :  2026. 02. 11',
        styles['CoverInfo']
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<b>버전</b>    :  v1.0',
        styles['CoverInfo']
    ))

    story.append(Spacer(1, 15*mm))

    # Key concepts
    concepts = [
        ['Agent', 'MCP', 'RAG', 'Collaboration'],
        ['자율적 품질 검증', '표준 통신 프로토콜', '영속적 지식 베이스', '팀 단위 작업 조율']
    ]
    concept_table = Table(concepts, colWidths=[35*mm]*4)
    concept_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TEXTCOLOR', (0, 0), (-1, 0), TEAL),
        ('FONTNAME', (0, 1), (-1, 1), FONT_REGULAR),
        ('FONTSIZE', (0, 1), (-1, 1), 7),
        ('TEXTCOLOR', (0, 1), (-1, 1), TEXT_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER_LIGHT),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER_LIGHT),
        ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER_LIGHT),
    ]))
    story.append(concept_table)

    # Switch to content template
    from reportlab.platypus import NextPageTemplate
    story.append(NextPageTemplate('Content'))
    story.append(PageBreak())

    # ===============================================
    # TABLE OF CONTENTS
    # ===============================================
    story.append(Paragraph('CONTENTS', styles['SectionNumber']))
    story.append(Paragraph('목차', styles['H1']))
    story.append(Spacer(1, 5*mm))

    toc_items = [
        ('01', '문제 인식: 바이브 코딩의 구조적 한계', '바이브 코딩의 이중 한계 — 모델 품질 격차와 협업의 벽'),
        ('02', '개선 아이디어: Agent-MCP-RAG 통합 협업 플랫폼', 'VIBE-X 5-Layer 아키텍처와 핵심 기술 통합'),
        ('03', '실무 적용 가능성', '단계별 로드맵과 팀 규모별 적용 전략'),
        ('04', '사고의 깊이 및 확장성', '구조적 관점, 장기 비전, 오픈소스 생태계'),
    ]

    for num, title, desc in toc_items:
        toc_data = [[
            Paragraph(f'<font color="#0D6E6E" size="20"><b>{num}</b></font>',
                      ParagraphStyle('tocn', alignment=TA_CENTER, fontName=FONT_BOLD)),
            Paragraph(f'<font size="12"><b>{title}</b></font><br/>'
                      f'<font size="8" color="{TEXT_LIGHT.hexval()}">{desc}</font>',
                      ParagraphStyle('toct', fontName=FONT_REGULAR, fontSize=12, leading=18, textColor=TEXT_PRIMARY))
        ]]
        toc_table = Table(toc_data, colWidths=[18*mm, CONTENT_WIDTH - 22*mm])
        toc_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ]))
        story.append(toc_table)
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ===============================================
    # SECTION 1: 문제 인식
    # ===============================================
    story.append(Paragraph('SECTION 01', styles['SectionNumber']))
    story.append(Paragraph('문제 인식: 바이브 코딩의 구조적 한계', styles['H1']))

    story.append(Paragraph('1.1 바이브 코딩이란?', styles['H2']))
    story.append(Paragraph(
        '바이브 코딩(Vibe Coding)은 개발자가 자연어로 의도를 전달하고 AI가 코드를 생성하는 새로운 개발 패러다임이다. '
        'Cursor, Windsurf, GitHub Copilot, Claude Code 등의 도구가 대표적이며, 코드를 직접 작성하지 않고 '
        'AI와 대화하며 개발한다는 점에서 기존 방식과 근본적으로 다르다.',
        styles['BodyText2']
    ))
    story.append(Paragraph(
        '그러나 이 혁명적 생산성 이면에는 <b>두 가지 축의 심각한 구조적 한계</b>가 존재한다.',
        styles['BodyText2']
    ))

    story.append(Paragraph('1.2 제1축 — 모델 품질 격차: "Memory-less Generation"', styles['H2']))
    story.append(Paragraph(
        '바이브 코딩의 결과물 품질은 사용하는 AI 모델의 성능에 크게 의존한다. 고성능 모델(Opus 급)은 '
        '아키텍처 수준의 설계 판단이 정확하고 보안/에러 처리가 자연스럽게 포함되나, 저비용 모델은 '
        '전체 일관성이 부족하고 이전 맥락을 소실한다. API 비용은 10~30배 차이가 난다.',
        styles['BodyText2']
    ))

    # Model comparison table
    model_data = [
        ['구분', '고성능 모델 (Opus 급)', '저비용 모델 (Sonnet/Haiku)'],
        ['아키텍처 설계', '정확한 판단', '전체 일관성 부족'],
        ['긴 컨텍스트', '일관성 유지', '이전 맥락 소실'],
        ['보안/에러 처리', '자연스럽게 포함', '빈번히 누락'],
        ['API 비용 (상대)', '10~30배', '1배 (기준)'],
    ]
    story.append(make_table(model_data, col_widths=[40*mm, 55*mm, 55*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        '더 근본적인 문제는 <b>"Just-in-Time Intelligence"</b> 구조이다. 생성하는 순간에는 똑똑하지만 '
        '세션이 종료되면 지능이 증발한다. 코드는 남지만 "왜 A 대신 B 패턴을 선택했는지"의 추론 과정은 사라진다.',
        styles['BodyText2']
    ))

    story.append(Paragraph('1.3 제2축 — 협업의 벽: Opus도 해결 못하는 문제', styles['H2']))
    story.append(Paragraph(
        '<b>고성능 모델을 사용하더라도</b> 팀 단위 협업에서는 해결 불가능한 구조적 결함이 존재한다.',
        styles['BodyText2']
    ))

    # Collaboration problems
    collab_problems = [
        ['문제', '설명', '영향'],
        ['컨텍스트 고립', '각 개발자의 AI 세션이 완전히 독립적', 'A는 JWT, B는 세션 인증 → 불일치'],
        ['아키텍처 분열', '각자 다른 패턴/라이브러리 선택', 'Redux vs Zustand, Axios vs fetch 공존'],
        ['암묵적 결정 소실', '설계 결정이 AI 대화 속에 매몰', '6개월 후 "왜?" 답변 불가'],
        ['동시 작업 충돌', 'AI의 대규모 파일 수정', 'Git merge 시 대규모 충돌'],
        ['품질 기준 파편화', '개인별 다른 품질 요구', '같은 프로젝트 내 품질 편차 극심'],
        ['온보딩 절벽', '맥락이 대화 속에만 존재', '새 팀원 온보딩 3~4주 소요'],
    ]
    story.append(make_table(collab_problems, col_widths=[35*mm, 55*mm, 55*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph('1.4 문제의 근본 원인 종합', styles['H2']))

    root_cause_data = [
        ['축', '핵심 원인', 'Opus 해결?', '시스템 해결?'],
        ['모델 품질', '컨텍스트 손실', '△', '○'],
        ['모델 품질', '암묵적 지식 부재', '○', '○'],
        ['모델 품질', '검증 부재', '✗', '○'],
        ['협업', '컨텍스트 고립', '✗', '○'],
        ['협업', '아키텍처 분열', '✗', '○'],
        ['협업', '암묵적 결정 소실', '✗', '○'],
        ['협업', '동시 작업 충돌', '✗', '○'],
        ['협업', '온보딩 절벽', '✗', '○'],
    ]
    story.append(make_table(root_cause_data, col_widths=[25*mm, 50*mm, 35*mm, 35*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(make_highlight_box(
        '<b>핵심 인사이트:</b> 모델 품질 문제는 부분적으로 고성능 모델로 완화 가능하지만, '
        '<b>협업 축의 6개 문제는 어떤 모델로도 해결되지 않는다.</b> '
        '이것이 바이브 코딩이 팀 프로젝트로 확장되지 못하는 근본 원인이다.',
        styles
    ))

    story.append(PageBreak())

    # ===============================================
    # SECTION 2: 개선 아이디어
    # ===============================================
    story.append(Paragraph('SECTION 02', styles['SectionNumber']))
    story.append(Paragraph('개선 아이디어: VIBE-X 통합 협업 플랫폼', styles['H1']))

    story.append(Paragraph('2.1 핵심 컨셉', styles['H2']))
    story.append(make_highlight_box(
        '<b>"개인의 AI 모델 성능을 올리는 것이 아니라, Agent + MCP + RAG + 협업 구조를 통합하여 '
        '팀의 AI 활용 환경을 구조화한다."</b>',
        styles
    ))
    story.append(Spacer(1, 3*mm))

    # 4 Technology pillars
    tech_data = [
        ['기술', '역할', '해결하는 문제'],
        ['Agent', '자율적 품질 검증 · 작업 조율 · 의사결정 추출', '검증 부재, 품질 파편화'],
        ['MCP', '도구 간 표준화된 통신 · 컨텍스트 공유 프로토콜', '컨텍스트 고립, 도구 파편화'],
        ['RAG', '코드베이스를 질문 가능한 지식 베이스로 전환', '의도 소실, 컨텍스트 손실'],
        ['협업 프로토콜', '팀 단위 작업 조율 · 충돌 방지 · 의사결정 동기화', '아키텍처 분열, 동시 작업 충돌'],
    ]
    story.append(make_table(tech_data, col_widths=[28*mm, 70*mm, 52*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('2.2 시스템 아키텍처 — 5-Layer 통합 구조', styles['H2']))

    # Architecture layers
    layers = [
        ('Layer 5', '팀 인텔리전스 대시보드', '프로젝트 건강 지표, 비용 관리, 온보딩 자동화'),
        ('Layer 4', '협업 오케스트레이터', 'MCP 기반 팀 컨텍스트 동기화, 충돌 사전 감지'),
        ('Layer 3', '멀티 Agent 품질 게이트', '자율 Agent 체인으로 6단계 품질 검증'),
        ('Layer 2', 'Living RAG Memory Engine', '코드베이스를 질문 가능한 지식 베이스로 전환'),
        ('Layer 1', '구조화 프롬프트 & 스캐폴딩', 'PACT-D 프레임워크, 팀 설계 청사진'),
    ]

    for i, (layer, name, desc) in enumerate(layers):
        bg_color = TEAL if i < 2 else BG_LIGHT
        text_color = white if i < 2 else TEXT_PRIMARY
        desc_color = HexColor('#B0DEDE') if i < 2 else TEXT_LIGHT

        layer_data = [[
            Paragraph(f'<font color="{text_color.hexval()}" size="8"><b>{layer}</b></font>',
                      ParagraphStyle('ln', alignment=TA_CENTER, fontName=FONT_BOLD)),
            Paragraph(f'<font color="{text_color.hexval()}" size="10"><b>{name}</b></font>',
                      ParagraphStyle('lname', fontName=FONT_BOLD, fontSize=10)),
            Paragraph(f'<font color="{desc_color.hexval()}" size="8">{desc}</font>',
                      ParagraphStyle('ld', fontName=FONT_REGULAR, fontSize=8)),
        ]]
        layer_table = Table(layer_data, colWidths=[22*mm, 50*mm, CONTENT_WIDTH - 76*mm])
        layer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        story.append(layer_table)
        story.append(Spacer(1, 1*mm))

    story.append(Paragraph(
        '<font color="#666666" size="8"><i>↕ MCP(Model Context Protocol) — 전체를 관통하는 통신 계층 ↕</i></font>',
        ParagraphStyle('mcp_note', alignment=TA_CENTER, fontName=FONT_REGULAR, fontSize=8)
    ))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('2.3 Layer 1: 구조화 프롬프트 & PACT-D 프레임워크', styles['H3']))
    pactd_data = [
        ['단계', '설명', '적용'],
        ['P (Purpose)', '이 코드가 해결하는 문제', '의도 명시'],
        ['A (Architecture)', '관련 파일, 기존 패턴, ADR 참조', '아키텍처 정합성'],
        ['C (Constraints)', '팀 코딩 규칙 자동 주입', '품질 표준화'],
        ['T (Test)', '성공 기준과 테스트 시나리오', '검증 가능성'],
        ['D (Dependency)', '다른 팀원 작업과의 의존성', '충돌 사전 방지'],
    ]
    story.append(make_table(pactd_data, col_widths=[35*mm, 55*mm, 55*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('2.4 Layer 2: Living RAG Memory Engine', styles['H3']))
    story.append(Paragraph(
        '기존 바이브 코딩의 <font color="#0D6E6E"><b>개발자 ↔ LLM</b></font> 단방향 통신을 '
        '<font color="#0D6E6E"><b>개발자 ↔ [Codebase Memory] ↔ LLM</b></font>의 순환 구조로 전환한다. '
        'AI 코드 생성 시 Hidden Intent File(.meta.json)을 동시에 생성하고, Git Hook을 통해 '
        'Vector DB(LanceDB/ChromaDB)에 자동 인덱싱한다.',
        styles['BodyText2']
    ))

    # RAG tech stack
    rag_data = [
        ['구분', '추천 도구', '선정 이유'],
        ['IDE 인터페이스', 'Continue.dev / Cursor', '오픈소스, RAG 지원, MCP 연동'],
        ['Vector DB', 'LanceDB / ChromaDB', '임베디드 모드, 무료, 빠른 속도'],
        ['임베딩 모델', 'Voyage-code-3', '코드 이해도 최상위'],
        ['Orchestration', 'LangChain / LlamaIndex', 'RAG 파이프라인 표준'],
        ['자동화', 'Git Hooks (Husky)', '커밋 시점 강제 인덱싱'],
    ]
    story.append(make_table(rag_data, col_widths=[35*mm, 50*mm, 65*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        '<b>memory.md 자동화 시스템</b>: 매 3회 대화마다 시스템이 기록 프롬프트를 자동 삽입하여 '
        'Sonnet의 컨텍스트 유지 능력이 수동 지시 Opus를 초과하게 된다. '
        '이것이 "시스템이 모델을 이기는" VIBE-X의 핵심 원리이다.',
        styles['BodyText2']
    ))

    # Memory comparison
    mem_data = [
        ['지표', '수동(Opus)', '수동(Sonnet)', '자동화(Sonnet)'],
        ['30분 후 기록 지속', '75%', '40%', '95%'],
        ['1시간 후 기록 지속', '60%', '15%', '95%'],
        ['팀 동기화율', '0%', '0%', '85%'],
    ]
    story.append(make_table(mem_data, col_widths=[38*mm, 32*mm, 32*mm, 38*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('2.5 Layer 3: 멀티 Agent 품질 게이트', styles['H3']))
    story.append(Paragraph(
        'AI가 생성한 코드를 <b>자율적 Agent 체인</b>이 6단계로 검증한다. '
        '각 Agent는 독립적으로 동작하며, MCP를 통해 검증 결과를 공유한다.',
        styles['BodyText2']
    ))

    gate_data = [
        ['Gate', 'Agent 역할', '검증 내용', '비용'],
        ['1', 'Syntax Agent', '린터 · 타입 검사', '$0'],
        ['2', 'Rules Agent', '팀 코딩 규칙 준수', '$0'],
        ['3', 'Integration Agent', '기존 테스트 통과', '저'],
        ['4', 'Review Agent', 'AI 교차 보안/성능 리뷰', '저'],
        ['5', 'Architecture Agent', 'ADR 정합성 · 타입 일관성', '$0'],
        ['6', 'Collision Agent', '팀원 작업 충돌 감지', '$0'],
    ]
    story.append(make_table(gate_data, col_widths=[15*mm, 35*mm, 55*mm, 25*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('2.6 Layer 4: MCP 기반 협업 오케스트레이터', styles['H3']))
    story.append(Paragraph(
        'MCP는 VIBE-X 전체를 관통하는 <b>표준 통신 프로토콜</b>이다. '
        '작업 영역 분리(Work Zone Isolation), 인터페이스 계약 선행(Interface-First Protocol), '
        '결정 자동 추출(Decision Auto-Extraction), 자동 핸드오프(Auto Handoff)를 가능하게 한다.',
        styles['BodyText2']
    ))

    story.append(Paragraph(
        '<b>작업 영역 분리:</b> 작업 시작 전 AI가 수정 예상 파일을 선언하고, MCP를 통해 팀 전체에 공유하여 '
        '충돌을 사전에 방지한다. <b>결정 자동 추출:</b> AI 대화에서 설계 결정 발생 시 Decision Extractor Agent가 '
        '자동 감지하여 팀 ADR에 반영하고 관련 팀원에게 알림한다.',
        styles['BodyText2']
    ))

    story.append(Paragraph('2.7 비용-효과 분석', styles['H2']))

    cost_data = [
        ['항목', 'Opus×5명\n(시스템 없음)', 'VIBE-X+Sonnet\n×5명', '절감률'],
        ['코드 생성', '$750', '$75', '90%'],
        ['Agent 리뷰', '—', '$15', '—'],
        ['RAG Indexing', '—', '$10', '—'],
        ['Decision Extraction', '—', '$8', '—'],
        ['월 총비용', '~$750', '~$108', '86%'],
    ]
    story.append(make_table(cost_data, col_widths=[35*mm, 38*mm, 38*mm, 25*mm]))
    story.append(Spacer(1, 3*mm))

    metric_data = [
        ['지표', 'Opus×5\n(시스템 없음)', 'VIBE-X\n+Sonnet×5'],
        ['개인 코드 품질', '90%', '85%'],
        ['아키텍처 일관성', '40%', '90%'],
        ['통합 충돌률', '45%', '12%'],
        ['설계 결정 추적률', '10%', '85%'],
        ['온보딩 시간', '2~3주', '2~3일'],
    ]
    story.append(make_table(metric_data, col_widths=[40*mm, 50*mm, 50*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(make_highlight_box(
        '<b>핵심:</b> 팀 환경에서 VIBE-X + Sonnet은 아키텍처 일관성(90% vs 40%)과 '
        '통합 충돌률(12% vs 45%)에서 Opus를 크게 앞선다.',
        styles
    ))

    story.append(PageBreak())

    # ===============================================
    # SECTION 3: 실무 적용 가능성
    # ===============================================
    story.append(Paragraph('SECTION 03', styles['SectionNumber']))
    story.append(Paragraph('실무 적용 가능성', styles['H1']))

    story.append(Paragraph('3.1 단계별 도입 로드맵', styles['H2']))

    # Phase cards
    phases = [
        ('Phase 1', '즉시 적용', '비용 $0 · 소요 3시간',
         '• project-definition.md, architecture-map.md, coding-rules.md 작성\n'
         '• Architecture Decision Record 운영 시작\n'
         '• PACT-D 프레임워크 수동 적용\n'
         '• .cursorrules에 memory.md 자동 기록 지시 추가'),
        ('Phase 2', '기반 구축', '비용 $0 · 소요 1~2주',
         '• 기존 코드베이스 전체 임베딩(Vector DB)\n'
         '• Git Hook으로 Gate 1~2, 5 자동 검증\n'
         '• 팀 상태 문서 수동 운영 시작\n'
         '• /gen-with-meta 커맨드로 메타데이터 습관화'),
        ('Phase 3', 'Agent 자동화', '소요 1~2개월',
         '• MCP 연동 — 팀 컨텍스트 자동 동기화\n'
         '• Quality Gate Agent 1~6 자동화\n'
         '• Decision Extractor Agent 구현\n'
         '• Git Hook 기반 자동 인덱싱 파이프라인'),
        ('Phase 4', '플랫폼화', '소요 3~6개월',
         '• 팀 인텔리전스 대시보드 웹 앱\n'
         '• IDE 플러그인(Cursor/VSCode 확장)\n'
         '• RAG 기반 온보딩 자동 브리핑\n'
         '• 피드백 루프 완전 자동화'),
    ]

    for phase_num, phase_name, phase_meta, phase_desc in phases:
        desc_lines = phase_desc.replace('\n', '<br/>')
        phase_data = [[
            Paragraph(f'<font color="#0D6E6E" size="14"><b>{phase_num}</b></font><br/>'
                      f'<font color="{TEXT_PRIMARY.hexval()}" size="10"><b>{phase_name}</b></font><br/>'
                      f'<font color="{TEXT_LIGHT.hexval()}" size="7">{phase_meta}</font>',
                      ParagraphStyle('pn', alignment=TA_CENTER, fontName=FONT_REGULAR, leading=16)),
            Paragraph(f'<font size="9" color="{TEXT_SECONDARY.hexval()}">{desc_lines}</font>',
                      ParagraphStyle('pd', fontName=FONT_REGULAR, fontSize=9, leading=14)),
        ]]
        phase_table = Table(phase_data, colWidths=[35*mm, CONTENT_WIDTH - 39*mm])
        phase_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), BG_LIGHT),
            ('BACKGROUND', (1, 0), (-1, -1), BG_WHITE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ('LINEBEFORE', (1, 0), (1, -1), 2, TEAL),
        ]))
        story.append(phase_table)
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 3*mm))

    story.append(Paragraph('3.2 팀 규모별 적용 전략', styles['H2']))
    team_data = [
        ['규모', '핵심 전략', '권장 Phase'],
        ['소규모 (2~5명)', '문서 기반 소통 + 선택적 자동화', 'Phase 1~3'],
        ['중규모 (6~15명)', '서브팀 구조 + 인터페이스 계약 필수', 'Phase 1~4 전체'],
        ['대규모 (15명+)', '전용 플랫폼 + 조직별 커스터마이징', 'Phase 4 확장'],
    ]
    story.append(make_table(team_data, col_widths=[35*mm, 65*mm, 45*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('3.3 기존 도구 통합', styles['H2']))
    tool_data = [
        ['도구', '통합 방법'],
        ['Cursor', '.cursorrules에 VIBE-X 규칙 통합, MCP 서버 연동'],
        ['Claude Code', 'CLAUDE.md에 규칙 통합, Hook 시스템으로 자동화'],
        ['GitHub/GitLab', 'PR 템플릿에 PACT-D 체크리스트, CI/CD에 Gate 통합'],
        ['Continue.dev', '@Codebase + @Memory 컨텍스트 활용'],
    ]
    story.append(make_table(tool_data, col_widths=[35*mm, CONTENT_WIDTH - 39*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('3.4 현실적 제약 고려', styles['H2']))

    constraints = [
        '<b>시간</b>: Phase 1~2는 팀 미팅 1회(3시간) + 설정 1일로 시작 가능',
        '<b>비용</b>: Phase 1~2는 비용 $0. Phase 3~4는 통합 충돌 재작업 비용 대비 2~3개월 내 ROI 달성',
        '<b>학습 곡선</b>: PACT-D 학습 1~2일, 팀 프로토콜 숙달 1~2주. 기존 Git 워크플로우를 보완',
        '<b>저항 관리</b>: 새 프로세스 추가가 아니라, 기존 암묵적 커뮤니케이션의 구조화',
    ]
    for c in constraints:
        story.append(Paragraph(f'  •  {c}', styles['BulletCustom']))

    story.append(PageBreak())

    # ===============================================
    # SECTION 4: 사고의 깊이 및 확장성
    # ===============================================
    story.append(Paragraph('SECTION 04', styles['SectionNumber']))
    story.append(Paragraph('사고의 깊이 및 확장성', styles['H1']))

    story.append(Paragraph('4.1 구조적 관점: 왜 "시스템"이 "모델"을 이기는가', styles['H2']))

    story.append(make_highlight_box(
        '<b>바이브 코딩의 미래는 "더 좋은 모델"이 아니라 "더 좋은 시스템"에 있다.</b>',
        styles
    ))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        '<b>현재:</b>  개인 → AI → 코드 (일회성, 고립된 생성)<br/>'
        '<b>VIBE-X:</b>  팀 → [Agent + MCP + RAG] → 구조화된 코드 (지속적, 연결된 생성)<br/>'
        '<b>미래:</b>  AI가 팀 협업 자체를 자율적으로 조율',
        styles['BodyText2']
    ))
    story.append(Spacer(1, 3*mm))

    principles = [
        '<b>Agent</b>는 사람이 놓치는 검증을 자율적으로 수행한다',
        '<b>MCP</b>는 고립된 도구들을 하나의 통합 생태계로 연결한다',
        '<b>RAG</b>는 휘발성 지능을 영속적 지식으로 전환한다',
        '<b>협업 프로토콜</b>은 개인 최적화를 팀 최적화로 확장한다',
    ]
    for p in principles:
        story.append(Paragraph(f'  •  {p}', styles['BulletCustom']))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('4.2 장기 비전: AI 협업의 새로운 패러다임', styles['H2']))

    vision_data = [
        ['단계', '설명', '시점'],
        ['현재', '개인이 AI에게 코드를 시킨다', 'Now'],
        ['단기', 'VIBE-X로 팀이 구조화된 환경에서 AI 사용', '3~6개월'],
        ['중기', 'Agent가 팀 협업을 자율적으로 조율', '1~2년'],
        ['장기', 'AI가 프로젝트 관리 자체를 지원하는 완전 자율 시스템', '2~3년'],
    ]
    story.append(make_table(vision_data, col_widths=[25*mm, 80*mm, 30*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('4.3 다른 영역으로의 확장', styles['H2']))

    expand_data = [
        ['영역', '적용 방식'],
        ['AI 팀 문서 작성', '스타일 · 용어 · 구조 일관성 유지'],
        ['AI 팀 디자인', '디자인 시스템 · 컴포넌트 규약 보장'],
        ['AI 데이터 분석', '지표 정의 · 계산 로직 · 해석 프레임워크 일관성'],
        ['AI 교육 콘텐츠', '교육 목표 · 난이도 · 평가 기준 표준화'],
    ]
    story.append(make_table(expand_data, col_widths=[40*mm, CONTENT_WIDTH - 44*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('4.4 오픈소스 생태계 비전', styles['H2']))

    story.append(Paragraph(
        'VIBE-X의 "공유 컨텍스트 + Agent 검증 + RAG 기억 + MCP 통신" 패턴을 오픈소스 생태계로 확장한다.',
        styles['BodyText2']
    ))

    eco_items = [
        '<b>Core Engine</b> — RAG Memory Manager, Agent Chain Runner, MCP Hub, Decision Extractor',
        '<b>IDE Plugins</b> — cursor-vibex, vscode-vibex, windsurf-vibex',
        '<b>Community Templates</b> — React+TS 규칙서, Next.js 아키텍처 맵, Python+FastAPI 설정',
        '<b>Knowledge Patterns</b> — 보안 취약점(200+), 성능 안티패턴(150+), React 공통 이슈(500+)',
    ]
    for item in eco_items:
        story.append(Paragraph(f'  •  {item}', styles['BulletCustom']))

    story.append(Spacer(1, 8*mm))

    # ===============================================
    # CONCLUSION
    # ===============================================
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL, spaceAfter=5*mm, spaceBefore=5*mm))

    story.append(Paragraph('결론', styles['H1']))

    story.append(Paragraph(
        '바이브 코딩의 이중 한계 — <b>모델 품질 격차</b>와 <b>팀 협업의 벽</b> — 는 단일 기술로는 해결할 수 없다.',
        styles['BodyText2']
    ))

    story.append(Paragraph(
        '<b>VIBE-X</b>는 <b>Agent</b>(자율 검증), <b>MCP</b>(표준 통신), <b>RAG</b>(영속 기억), '
        '<b>협업 프로토콜</b>(팀 조율)의 네 가지 기술을 5-Layer 구조로 통합하여, '
        '이 이중 한계를 동시에 해결한다.',
        styles['BodyText2']
    ))

    story.append(Paragraph(
        'Phase 1~2는 <b>비용 $0으로 즉시 적용 가능</b>하며, 점진적으로 Agent 자동화와 플랫폼화로 확장된다. '
        '이 시스템이 오픈소스 생태계로 성장하면, 바이브 코딩은 개인의 생산성 도구에서 '
        '<b>팀의 협업 인프라</b>로 진화할 것이다.',
        styles['BodyText2']
    ))

    story.append(Spacer(1, 5*mm))

    story.append(make_highlight_box(
        '<b>"바이브 코딩의 다음 단계는 더 좋은 모델이 아니라, 더 좋은 시스템에 있다."</b>',
        styles
    ))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="30%", thickness=1, color=BORDER_LIGHT, spaceAfter=3*mm, hAlign='CENTER'))
    story.append(Paragraph(
        '<i>팀 바이브제왕  |  2026. 02. 11</i>',
        ParagraphStyle('sig', alignment=TA_CENTER, fontName=FONT_REGULAR, fontSize=9, textColor=TEXT_LIGHT)
    ))

    # Build
    doc.build(story)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == '__main__':
    build_document()

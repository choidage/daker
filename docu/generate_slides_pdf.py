# -*- coding: utf-8 -*-
"""
바이브코딩 개선 아이디어 — 피그마 스타일 슬라이드 PDF 생성 (v2 - 큰 글씨)
팀 바이브제왕 | 2026.02.11
"""

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
import os

# === Font Registration ===
FONT_PATH = 'C:/Windows/Fonts/'
pdfmetrics.registerFont(TTFont('MalgunGothic', FONT_PATH + 'malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunGothicBold', FONT_PATH + 'malgunbd.ttf'))
pdfmetrics.registerFont(TTFont('MalgunGothicLight', FONT_PATH + 'malgunsl.ttf'))
registerFontFamily('MalgunGothic', normal='MalgunGothic', bold='MalgunGothicBold',
                    italic='MalgunGothicLight', boldItalic='MalgunGothicBold')

F = 'MalgunGothic'
FB = 'MalgunGothicBold'

# === Colors ===
TEAL      = HexColor('#0D6E6E')
TEAL_DARK = HexColor('#0A5A5A')
TEAL_2    = HexColor('#0E7D7D')
TEAL_3    = HexColor('#10908E')
TEAL_4    = HexColor('#14A3A0')
TEAL_5    = HexColor('#1AB5B0')
TEAL_BG   = HexColor('#F0F8F8')
TEAL_TXT  = HexColor('#B0DEDE')
DARK      = HexColor('#0D0D0D')
WHITE     = HexColor('#FFFFFF')
GRAY      = HexColor('#7A7A7A')
BORDER    = HexColor('#E8E8E8')
GBGC      = HexColor('#FAFAFA')
ORANGE    = HexColor('#E07B54')
GREEN     = HexColor('#22C55E')
MUTED     = HexColor('#B0B0B0')
D333      = HexColor('#333333')
D555      = HexColor('#555555')

# === Page: Standard 16:9 presentation (inches: ~14 x 7.88) ===
PW = 1008  # points
PH = 567   # points (16:9 ratio)

OUTPUT = os.path.join(os.path.dirname(__file__), '바이브코딩_슬라이드.pdf')

# === Drawing Helpers ===
def rect(c, x, y, w, h, fill=None, stroke=None, sw=0.5):
    ry = PH - y - h
    if fill:
        c.setFillColor(fill)
        c.rect(x, ry, w, h, fill=1, stroke=0)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(sw)
        c.rect(x, ry, w, h, fill=0, stroke=1)

def txt(c, s, x, y, font=F, sz=12, color=DARK, anchor='l'):
    ry = PH - y
    c.setFont(font, sz)
    c.setFillColor(color)
    if anchor == 'r':
        c.drawRightString(x, ry, s)
    elif anchor == 'c':
        c.drawCentredString(x, ry, s)
    else:
        c.drawString(x, ry, s)

def dot_item(c, label, x, y, dot_color=TEAL, sz=10, gap=6):
    rect(c, x, y - 1, 4, 4, fill=dot_color)
    txt(c, label, x + gap + 4, y, F, sz, DARK)


# ============================================================
#  SLIDE 1 — COVER
# ============================================================
def slide_cover(c):
    c.setPageSize((PW, PH))
    rect(c, 0, 0, PW, PH, fill=WHITE)

    # Top teal bar
    rect(c, 0, 0, PW, 4, fill=TEAL)

    # Right panel
    rpw = 300
    rpx = PW - rpw
    rect(c, rpx, 0, rpw, PH, fill=TEAL)

    # Left content
    lx = 56
    ly = 70

    txt(c, 'PROPOSAL  |  2026. 02. 11', lx, ly, F, 9, TEAL)

    ly += 38
    txt(c, '바이브코딩', lx, ly, FB, 42, DARK)
    ly += 50
    txt(c, '개선 아이디어', lx, ly, FB, 42, DARK)

    ly += 44
    txt(c, 'Agent + MCP + RAG + Collaboration 통합을 통한', lx, ly, F, 12, GRAY)
    ly += 20
    txt(c, '바이브 코딩의 구조적 한계 극복 전략', lx, ly, F, 12, GRAY)

    ly += 30
    rect(c, lx, ly, 44, 2.5, fill=TEAL)

    ly += 22
    txt(c, '제안자 :  팀 바이브제왕', lx, ly, F, 10, GRAY)
    ly += 18
    txt(c, '버전 :  v1.0', lx, ly, F, 10, GRAY)

    # Right panel cards
    rx = rpx + 32
    ry = 60
    cw = rpw - 64
    txt(c, 'CORE TECHNOLOGIES', rx, ry, F, 8, TEAL_TXT)

    cards = [
        ('Agent', '자율적 품질 검증 · 작업 조율 · 의사결정 추출'),
        ('MCP', '도구 간 표준화된 통신 · 컨텍스트 공유 프로토콜'),
        ('RAG', '코드베이스를 질문 가능한 지식 베이스로 전환'),
        ('Collaboration', '팀 단위 작업 조율 · 충돌 방지 · 의사결정 동기화'),
    ]
    ry += 24
    ch = 82
    for title, desc in cards:
        rect(c, rx, ry, cw, ch, fill=TEAL_DARK)
        txt(c, title, rx + 16, ry + 22, FB, 15, WHITE)
        txt(c, desc, rx + 16, ry + 44, F, 9, TEAL_TXT)
        ry += ch + 16


# ============================================================
#  SLIDE 2 — PROBLEM
# ============================================================
def slide_problem(c):
    c.setPageSize((PW, PH))
    rect(c, 0, 0, PW, PH, fill=WHITE)

    lx = 56
    ly = 40

    # Header
    txt(c, '01', lx, ly + 6, FB, 36, TEAL)
    txt(c, '문제 인식 — 바이브 코딩의 이중 한계', lx + 48, ly, FB, 20, DARK)
    txt(c, 'AI 코드 생성의 현재 한계를 두 가지 축으로 분석합니다', lx + 48, ly + 26, F, 10, GRAY)

    ly += 56
    rect(c, lx, ly, PW - 112, 1, fill=BORDER)

    # Two columns
    ly += 16
    col_gap = 28
    col_w = (PW - 112 - col_gap) / 2
    box_h = PH - ly - 24

    # Box A
    bx = lx
    rect(c, bx, ly, col_w, box_h, stroke=BORDER, sw=0.7)

    by = ly + 20
    txt(c, '한계 A', bx + 20, by, FB, 9, TEAL)
    by += 22
    txt(c, '모델 품질 격차', bx + 20, by, FB, 17, DARK)
    by += 28
    txt(c, '저비용 모델(Sonnet, GPT-4o-mini)은 고비용 모델', bx + 20, by, F, 10, GRAY)
    by += 16
    txt(c, '(Opus, o1-pro)에 비해 코드 품질이 크게 떨어지지만,', bx + 20, by, F, 10, GRAY)
    by += 16
    txt(c, '비용 현실 때문에 대부분의 팀이 저비용 모델을 사용합니다.', bx + 20, by, F, 10, GRAY)

    by += 30
    for item in ['아키텍처 일관성 유지 실패', '엣지 케이스 처리 누락', '보안 취약점 자동 생성', '기존 코드와의 통합 부조화']:
        dot_item(c, item, bx + 20, by, TEAL, 10)
        by += 22

    # Box B
    bx2 = lx + col_w + col_gap
    rect(c, bx2, ly, col_w, box_h, stroke=BORDER, sw=0.7)

    by = ly + 20
    txt(c, '한계 B', bx2 + 20, by, FB, 9, ORANGE)
    by += 22
    txt(c, '협업 구조 부재', bx2 + 20, by, FB, 17, DARK)
    by += 28
    txt(c, 'Opus급 모델을 사용해도 해결할 수 없는 구조적 문제.', bx2 + 20, by, F, 10, GRAY)
    by += 16
    txt(c, '여러 명이 AI를 동시에 사용할 때 발생하는', bx2 + 20, by, F, 10, GRAY)
    by += 16
    txt(c, '협업 파괴 현상입니다.', bx2 + 20, by, F, 10, GRAY)

    by += 30
    for item in ['컨텍스트 고립 (Context Isolation)', '아키텍처 발산 (Architecture Divergence)', '암묵적 의사결정 유실 (Tacit Decision Loss)', '지식 증발 (Knowledge Evaporation)']:
        dot_item(c, item, bx2 + 20, by, ORANGE, 10)
        by += 22


# ============================================================
#  SLIDE 3 — SOLUTION (5-Layer Architecture)
# ============================================================
def slide_solution(c):
    c.setPageSize((PW, PH))
    rect(c, 0, 0, PW, PH, fill=WHITE)

    lx = 56
    ly = 36

    txt(c, '02', lx, ly + 6, FB, 36, TEAL)
    txt(c, 'VIBE-X — 5-Layer 통합 아키텍처', lx + 48, ly, FB, 20, DARK)
    txt(c, 'Agent + MCP + RAG + 협업 프로토콜을 통합한 구조적 솔루션', lx + 48, ly + 26, F, 10, GRAY)

    ly += 56
    rect(c, lx, ly, PW - 112, 1, fill=BORDER)

    # Layers
    ly += 12
    rpw = 270
    layer_w = PW - 112 - rpw - 20
    avail_h = PH - ly - 20
    layer_h = (avail_h - 28) / 5  # 28 for mcp bar

    layers = [
        ('L5', '팀 인텔리전스 대시보드', '프로젝트 건강 지표 · 비용 관리 · 온보딩 자동화', TEAL),
        ('L4', '협업 오케스트레이터 (MCP 기반)', '팀 컨텍스트 동기화 · 충돌 사전 감지 · 결정 자동 추출', TEAL_2),
        ('L3', '멀티 Agent 품질 게이트', '자율 Agent 체인으로 6단계 품질 검증 파이프라인', TEAL_3),
        ('L2', 'Living RAG Memory Engine', '코드베이스를 질문 가능한 지식 베이스로 전환', TEAL_4),
        ('L1', '구조화 프롬프트 & 프로젝트 스캐폴딩', 'PACT-D 프레임워크 · 팀 설계 청사진 (Single Source of Truth)', TEAL_5),
    ]
    cy = ly
    for num, title, desc, color in layers:
        rect(c, lx, cy, layer_w, layer_h, fill=color)
        txt(c, num, lx + 14, cy + layer_h / 2 - 1, FB, 10, TEAL_TXT)
        txt(c, title, lx + 38, cy + layer_h / 2 - 8, FB, 11, WHITE)
        txt(c, desc, lx + 38, cy + layer_h / 2 + 8, F, 8, TEAL_TXT)
        cy += layer_h

    rect(c, lx, cy, layer_w, 28, fill=DARK)
    txt(c, 'MCP (Model Context Protocol) — 전체를 관통하는 통신 계층', lx + layer_w / 2, cy + 10, FB, 9, WHITE, 'c')

    # Right panel
    rpx = lx + layer_w + 20
    rpy = ly

    # Cost box
    cbh = 180
    rect(c, rpx, rpy, rpw, cbh, stroke=BORDER, sw=0.7)
    by = rpy + 16
    txt(c, '비용-효과 비교', rpx + 16, by, FB, 8, TEAL)
    by += 22
    txt(c, '월 비용 (5인 팀)', rpx + 16, by, FB, 14, DARK)
    by += 28
    txt(c, 'Opus × 5 (시스템 없음)', rpx + 16, by, F, 10, GRAY)
    txt(c, '~$750', rpx + rpw - 16, by, FB, 14, GRAY, 'r')
    by += 26
    txt(c, 'VIBE-X + Sonnet × 5', rpx + 16, by, F, 10, DARK)
    txt(c, '~$108', rpx + rpw - 16, by, FB, 14, TEAL, 'r')
    by += 28
    rect(c, rpx + 12, by, rpw - 24, 24, fill=TEAL_BG)
    txt(c, '86% 비용 절감', rpx + rpw / 2, by + 8, FB, 11, TEAL, 'c')

    # KPI box
    rpy2 = rpy + cbh + 14
    kbh = PH - rpy2 - 20
    rect(c, rpx, rpy2, rpw, kbh, stroke=BORDER, sw=0.7)
    by = rpy2 + 16
    txt(c, '핵심 지표 비교', rpx + 16, by, FB, 8, TEAL)

    kpis = [('아키텍처 일관성', '40%', '90%'), ('통합 충돌률', '45%', '12%'),
            ('설계 결정 추적률', '10%', '85%'), ('온보딩 시간', '2~3주', '2~3일')]
    by += 24
    for label, old, new in kpis:
        txt(c, label, rpx + 16, by, F, 10, GRAY)
        rx = rpx + rpw - 16
        txt(c, new, rx, by, FB, 11, GREEN, 'r')
        nw = c.stringWidth(new, FB, 11)
        txt(c, '  →  ', rx - nw - 4, by, F, 9, GRAY, 'r')
        aw = c.stringWidth('  →  ', F, 9)
        txt(c, old, rx - nw - aw - 4, by, F, 10, MUTED, 'r')
        by += 28


# ============================================================
#  SLIDE 4 — ROADMAP
# ============================================================
def slide_roadmap(c):
    c.setPageSize((PW, PH))
    rect(c, 0, 0, PW, PH, fill=WHITE)

    lx = 56
    ly = 36

    txt(c, '03', lx, ly + 6, FB, 36, TEAL)
    txt(c, '단계별 구현 로드맵', lx + 48, ly, FB, 20, DARK)
    txt(c, 'Phase 1~4를 통한 점진적 도입 — 비용 $0에서 시작하여 플랫폼화까지', lx + 48, ly + 26, F, 10, GRAY)

    ly += 56
    rect(c, lx, ly, PW - 112, 1, fill=BORDER)

    ly += 14
    cgap = 14
    cw = (PW - 112 - 3 * cgap) / 4
    ch = PH - ly - 24

    phases = [
        ('Phase 1', '$0', '즉시 적용', '소요: 3시간',
         ['프로젝트 정의서 작성', '아키텍처 맵 작성', 'PACT-D 프롬프트 도입', 'memory.md 자동화', 'ADR 운영 시작'], True),
        ('Phase 2', '$0', '기반 구축', '소요: 1~2주',
         ['RAG 초기화 (Vector DB)', 'Git Hook 설정', 'Gate 1~2 자동 검증', '메타데이터 포집 습관화'], False),
        ('Phase 3', '개발비', 'Agent 자동화', '소요: 1~2개월',
         ['MCP 서버 연동', 'Quality Gate Agent 1~6', 'Decision Extractor 구현', 'RAG 자동 인덱싱 파이프라인'], False),
        ('Phase 4', '인프라비', '플랫폼화', '소요: 3~6개월',
         ['팀 대시보드 웹 앱', 'IDE 플러그인 개발', '온보딩 자동화', '오픈소스 생태계 공개'], False),
    ]

    cx = lx
    for num, cost, title, time_, items, active in phases:
        sc = TEAL if active else BORDER
        sw = 1.2 if active else 0.7
        rect(c, cx, ly, cw, ch, stroke=sc, sw=sw)

        by = ly + 16
        # Badge
        bw = c.stringWidth(num, FB, 9) + 14
        if active:
            rect(c, cx + 14, by - 4, bw, 18, fill=TEAL)
            txt(c, num, cx + 14 + 7, by + 1, FB, 9, WHITE)
        else:
            rect(c, cx + 14, by - 4, bw, 18, fill=GBGC, stroke=BORDER, sw=0.4)
            txt(c, num, cx + 14 + 7, by + 1, FB, 9, DARK)

        if cost.startswith('$'):
            txt(c, cost, cx + cw - 14, by + 1, FB, 13, TEAL, 'r')
        else:
            txt(c, cost, cx + cw - 14, by + 2, F, 9, GRAY, 'r')

        by += 30
        txt(c, title, cx + 14, by, FB, 14, DARK)
        by += 20
        txt(c, time_, cx + 14, by, F, 9, GRAY)
        by += 16
        rect(c, cx + 14, by, cw - 28, 0.5, fill=BORDER)

        by += 14
        for item in items:
            rect(c, cx + 14, by, 4, 4, fill=TEAL)
            txt(c, item, cx + 24, by - 1, F, 9, DARK)
            by += 18

        cx += cw + cgap


# ============================================================
#  SLIDE 5 — CONCLUSION
# ============================================================
def slide_conclusion(c):
    c.setPageSize((PW, PH))
    rect(c, 0, 0, PW, PH, fill=DARK)

    rect(c, 0, 0, PW, 4, fill=TEAL)

    lx = 56
    ly = 60

    txt(c, '"', lx, ly, FB, 60, TEAL)

    ly += 48
    txt(c, '바이브 코딩의 다음 단계는', lx, ly, FB, 28, WHITE)
    ly += 38
    txt(c, '더 좋은 모델이 아니라,', lx, ly, FB, 28, WHITE)
    ly += 38
    txt(c, '더 좋은 시스템에 있다.', lx, ly, FB, 28, WHITE)

    ly += 32
    txt(c, 'The next step for vibe coding lies not in better models, but in better systems.', lx, ly, F, 10, GRAY)

    ly += 34
    rect(c, lx, ly, 44, 2.5, fill=TEAL)

    # 4 pillars
    ly += 24
    pgap = 16
    pw_ = (PW - 112 - 3 * pgap) / 4
    ph_ = 76

    pillars = [
        ('Agent', '사람이 놓치는 검증을', '자율적으로 수행'),
        ('MCP', '고립된 도구들을 하나의', '통합 생태계로 연결'),
        ('RAG', '휘발성 지능을', '영속적 지식으로 전환'),
        ('Collaboration', '개인 최적화를', '팀 최적화로 확장'),
    ]
    px = lx
    for title, l1, l2 in pillars:
        rect(c, px, ly, pw_, ph_, stroke=D333, sw=0.5)
        txt(c, title, px + 16, ly + 22, FB, 12, TEAL)
        txt(c, l1, px + 16, ly + 40, F, 9, GRAY)
        txt(c, l2, px + 16, ly + 54, F, 9, GRAY)
        px += pw_ + pgap

    # Footer
    fy = PH - 36
    txt(c, '팀 바이브제왕', lx, fy, FB, 10, GRAY)
    txt(c, '2026. 02. 11', lx, fy + 16, F, 9, D555)
    txt(c, 'VIBE-X', PW - 56, fy, FB, 14, TEAL, 'r')
    txt(c, 'v1.0', PW - 56, fy + 16, F, 9, D555, 'r')


# ============================================================
#  MAIN
# ============================================================
def main():
    c = canvas.Canvas(OUTPUT, pagesize=(PW, PH))
    c.setTitle('바이브코딩 개선 아이디어 — 팀 바이브제왕')
    c.setAuthor('팀 바이브제왕')

    slide_cover(c);    c.showPage()
    slide_problem(c);  c.showPage()
    slide_solution(c); c.showPage()
    slide_roadmap(c);  c.showPage()
    slide_conclusion(c); c.showPage()

    c.save()
    sz = os.path.getsize(OUTPUT)
    print(f'PDF 생성 완료: {OUTPUT}')
    print(f'파일 크기: {sz:,} bytes')
    print(f'총 5장 슬라이드 | 페이지: {PW}x{PH}pt')

if __name__ == '__main__':
    main()

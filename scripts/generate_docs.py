"""Generate ERP System documentation PDFs (English).

Usage:
    python -m scripts.generate_docs          # generates all 4 PDFs
    python -m scripts.generate_docs 1        # generates only PDF #1

Output:
    docs/01_ERP_System_Documentation.pdf
    docs/02_Feasibility_Study_Pricing.pdf
    docs/03_Deployment_Guide.pdf
    docs/04_User_Manual.pdf
"""

import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    KeepTogether,
)

# ---------------------------------------------------------------------------
# Font setup
# ---------------------------------------------------------------------------
FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "tahoma.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuBold", os.path.join(FONT_DIR, "tahomabd.ttf")))

F = "DejaVu"
FB = "DejaVuBold"
H = "Helvetica"
HB = "Helvetica-Bold"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
PRIMARY = colors.HexColor("#4F46E5")
PRIMARY_DARK = colors.HexColor("#3730A3")
PRIMARY_LIGHT = colors.HexColor("#EEF2FF")
SUCCESS = colors.HexColor("#10B981")
DANGER = colors.HexColor("#EF4444")
WARNING = colors.HexColor("#F59E0B")
DARK = colors.HexColor("#1E293B")
GRAY = colors.HexColor("#64748B")
LIGHT_BG = colors.HexColor("#F8FAFC")
WHITE = colors.white


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def S():
    """All paragraph styles."""
    d = {}
    d["cover_title"] = ParagraphStyle("ct", fontName=HB, fontSize=32, leading=40,
                                       textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=6)
    d["cover_sub"] = ParagraphStyle("cs", fontName=H, fontSize=14, leading=20,
                                     textColor=GRAY, alignment=TA_CENTER, spaceAfter=4)
    d["cover_version"] = ParagraphStyle("cv", fontName=H, fontSize=11, leading=14,
                                         textColor=GRAY, alignment=TA_CENTER)
    d["toc"] = ParagraphStyle("toc", fontName=H, fontSize=11, leading=18, textColor=DARK,
                               leftIndent=20, spaceAfter=2)
    d["h1"] = ParagraphStyle("h1", fontName=HB, fontSize=18, leading=24, textColor=DARK,
                              spaceBefore=20, spaceAfter=10)
    d["h2"] = ParagraphStyle("h2", fontName=HB, fontSize=14, leading=19, textColor=PRIMARY,
                              spaceBefore=14, spaceAfter=7)
    d["h3"] = ParagraphStyle("h3", fontName=HB, fontSize=11, leading=15, textColor=DARK,
                              spaceBefore=10, spaceAfter=5)
    d["body"] = ParagraphStyle("body", fontName=H, fontSize=10, leading=15, textColor=DARK,
                                alignment=TA_JUSTIFY, spaceAfter=6)
    d["body_left"] = ParagraphStyle("bl", fontName=H, fontSize=10, leading=15, textColor=DARK,
                                     spaceAfter=6)
    d["bullet"] = ParagraphStyle("bul", fontName=H, fontSize=10, leading=15, textColor=DARK,
                                  leftIndent=20, bulletIndent=6, spaceAfter=3,
                                  bulletFontName=HB, bulletFontSize=10)
    d["sub_bullet"] = ParagraphStyle("sbul", fontName=H, fontSize=9, leading=13,
                                      textColor=GRAY, leftIndent=36, bulletIndent=24, spaceAfter=2)
    d["code"] = ParagraphStyle("code", fontName="Courier", fontSize=9, leading=13,
                                textColor=colors.HexColor("#334155"),
                                backColor=LIGHT_BG, borderPadding=8,
                                spaceBefore=4, spaceAfter=4)
    d["th"] = ParagraphStyle("th", fontName=HB, fontSize=9, leading=12,
                              textColor=WHITE, alignment=TA_CENTER)
    d["td"] = ParagraphStyle("td", fontName=H, fontSize=9, leading=12,
                              textColor=DARK, alignment=TA_CENTER)
    d["td_left"] = ParagraphStyle("tdl", fontName=H, fontSize=9, leading=12,
                                   textColor=DARK, alignment=TA_LEFT)
    d["note"] = ParagraphStyle("note", fontName=H, fontSize=9, leading=13,
                                textColor=PRIMARY_DARK, backColor=PRIMARY_LIGHT,
                                borderPadding=8, spaceBefore=4, spaceAfter=4)
    d["warning"] = ParagraphStyle("warn", fontName=HB, fontSize=9, leading=13,
                                   textColor=colors.HexColor("#92400E"),
                                   backColor=colors.HexColor("#FEF3C7"),
                                   borderPadding=8, spaceBefore=4, spaceAfter=4)
    d["footer"] = ParagraphStyle("foot", fontName=H, fontSize=8, leading=10,
                                  textColor=GRAY, alignment=TA_CENTER)
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hr():
    return HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E1"),
                       spaceBefore=6, spaceAfter=6)


def build_table(headers, rows, col_widths=None):
    s = S()
    data = [[Paragraph(h, s["th"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), s["td"]) if not isinstance(c, Paragraph) else c for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("TOPPADING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build_table_left(headers, rows, col_widths=None):
    s = S()
    data = [[Paragraph(h, s["th"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), s["td_left"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(H, 8)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(A4[0] / 2, 1.5 * cm,
                              f"ERP Pro — Confidential  |  Page {doc.page}")
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(2 * cm, A4[1] - 1.8 * cm, A4[0] - 2 * cm, A4[1] - 1.8 * cm)
    canvas.restoreState()


def make_doc(path, title):
    return SimpleDocTemplate(path, pagesize=A4,
                              topMargin=2.5 * cm, bottomMargin=2.5 * cm,
                              leftMargin=2 * cm, rightMargin=2 * cm,
                              title=title, author="ERP Pro")


# ===========================================================================
# PDF 1 — System Documentation
# ===========================================================================

def build_pdf1(path):
    doc = make_doc(path, "ERP Pro — System Documentation")
    s = S()
    st = []

    # ── Cover ──
    st.append(Spacer(1, 6 * cm))
    st.append(Paragraph("ERP Pro", s["cover_title"]))
    st.append(Paragraph("Complete System Documentation", s["cover_sub"]))
    st.append(Spacer(1, 1 * cm))
    st.append(Paragraph("Version 1.0  •  August 2026", s["cover_version"]))
    st.append(Paragraph("Proprietary — Internal Use Only", s["cover_version"]))
    st.append(PageBreak())

    # ── Table of Contents ──
    st.append(Paragraph("Table of Contents", s["h1"]))
    st.append(hr())
    toc_items = [
        "1. Introduction",
        "2. Technical Architecture",
        "3. Database Design",
        "4. Modules Overview",
        "5. Role-Based Access Control (RBAC)",
        "6. Security Model",
        "7. Competitive Analysis",
        "8. Complete API Reference",
    ]
    for item in toc_items:
        st.append(Paragraph(item, s["toc"]))
    st.append(PageBreak())

    # ── 1. Introduction ──
    st.append(Paragraph("1. Introduction", s["h1"]))
    st.append(hr())
    st.append(Paragraph(
        "ERP Pro is a comprehensive, multi-company, multi-branch Enterprise Resource Planning system "
        "built with modern web technologies. It provides a unified platform for managing the complete "
        "business lifecycle: from sales and purchasing through inventory management, accounting, human "
        "resources, point of sale, project management, and manufacturing.",
        s["body"]))
    st.append(Paragraph(
        "The system is designed as a SaaS-ready platform that can be self-hosted or deployed in the "
        "cloud. It features a professional dark-mode UI with full bilingual support (Arabic and English), "
        "granular role-based access control with 63 permission codes, and a modular architecture where "
        "companies only enable the modules they need.",
        s["body"]))

    st.append(Paragraph("Key System Statistics", s["h2"]))
    st.append(build_table(
        ["Metric", "Value", "Description"],
        [
            ["API Endpoints", "~120", "RESTful endpoints across 18 routers"],
            ["Database Tables", "40+", "PostgreSQL tables with full referential integrity"],
            ["Permission Codes", "63", "Granular view/manage/delete per module"],
            ["Licensed Modules", "8", "Sales, Purchases, Inventory, Accounting, HR, POS, Projects, Manufacturing"],
            ["Test Coverage", "110 + 24", "110 unit/integration tests + 24 E2E browser tests"],
            ["Languages", "2", "English and Arabic with RTL support"],
            ["ORM Models", "40+", "SQLAlchemy 2.0 declarative models"],
        ],
        col_widths=[3.5 * cm, 2.5 * cm, 11 * cm]
    ))

    st.append(Paragraph("Design Principles", s["h2"]))
    principles = [
        ("Multi-Tenant First", "Every business table has a company_id foreign key. All queries are automatically filtered by the authenticated user's current company. Users can belong to multiple companies with different roles in each."),
        ("Module Licensing", "Each company has an enabled_modules list. The require_module dependency checks this before granting access to module-specific endpoints. Superusers bypass this check."),
        ("Fail-Open Design", "Redis outages do not block logins (rate limiting degrades gracefully). Email failures are logged but never crash the application. The system is designed to remain operational under partial infrastructure failures."),
        ("Convention Over Configuration", "Auto-generated sequential codes for invoices, work orders, projects. Weighted-average costing calculated automatically on purchase confirmation. Stock adjustments posted automatically on stock take completion."),
    ]
    for title, desc in principles:
        st.append(Paragraph(title, s["h3"]))
        st.append(Paragraph(desc, s["body"]))
    st.append(PageBreak())

    # ── 2. Technical Architecture ──
    st.append(Paragraph("2. Technical Architecture", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Technology Stack", s["h2"]))
    st.append(build_table(
        ["Layer", "Technology", "Version", "Purpose"],
        [
            ["Backend Framework", "FastAPI", "0.115+", "Async REST API with automatic OpenAPI docs"],
            ["ORM", "SQLAlchemy", "2.0", "Declarative models with type hints"],
            ["Migrations", "Alembic", "1.14+", "Zero-downtime schema migrations"],
            ["Database", "PostgreSQL", "16", "Primary data store with full ACID compliance"],
            ["Cache / Queue", "Redis", "7", "Rate limiting, session caching, pub/sub"],
            ["Frontend Framework", "React", "19", "Component-based SPA with hooks"],
            ["Build Tool", "Vite", "8", "Fast HMR and optimized production builds"],
            ["HTTP Client", "Axios", "1.7+", "API communication with interceptors"],
            ["Routing", "React Router", "7", "Client-side routing with lazy loading"],
            ["Containerization", "Docker", "24+", "Reproducible builds and deployments"],
            ["Reverse Proxy", "Nginx", "1.27", "SPA serving + API proxy in production"],
            ["Testing", "pytest", "9+", "Unit, integration, and E2E testing"],
            ["PDF Generation", "ReportLab", "4+", "Professional documentation generation"],
        ],
        col_widths=[3 * cm, 3 * cm, 2 * cm, 9 * cm]
    ))

    st.append(Paragraph("System Architecture Diagram", s["h2"]))
    st.append(Paragraph(
        "The system follows a classic three-tier architecture with clear separation of concerns:",
        s["body"]))
    st.append(Paragraph(
        "┌─────────────────────────────────────────────────────────────────┐<br/>"
        "│                        CLIENT LAYER                             │<br/>"
        "│  Browser → React SPA (Vite build) → Nginx (port 80/443)         │<br/>"
        "│  Serves: index.html, JS bundles, CSS, static assets             │<br/>"
        "│  Proxies: /api/* → http://web:8000                              │<br/>"
        "└────────────────────────────┬────────────────────────────────────┘<br/>"
        "                             │ HTTP                                │<br/>"
        "┌────────────────────────────▼────────────────────────────────────┐<br/>"
        "│                        API LAYER                                │<br/>"
        "│  FastAPI (uvicorn, port 8000)                                    │<br/>"
        "│  Auth → RBAC → Module → Service → Router                        │<br/>"
        "│  Dependencies: get_db, get_current_user, require_permission     │<br/>"
        "│                require_module, get_current_company_id            │<br/>"
        "└────────────────────────────┬────────────────────────────────────┘<br/>"
        "                             │ SQL                                 │<br/>"
        "┌────────────────────────────▼────────────────────────────────────┐<br/>"
        "│                        DATA LAYER                               │<br/>"
        "│  PostgreSQL 16 (primary)  +  Redis 7 (cache/rate-limit)         │<br/>"
        "│  40+ tables, FK constraints, auto-numbering sequences           │<br/>"
        "└─────────────────────────────────────────────────────────────────┘",
        s["code"]))

    st.append(Paragraph("Request Flow", s["h2"]))
    steps = [
        "1. Client sends HTTP request to Nginx (port 80/443)",
        "2. Nginx proxies /api/* to FastAPI backend (port 8000)",
        "3. FastAPI extracts bearer token from Authorization header",
        "4. get_current_user dependency validates token → returns User",
        "5. get_current_company_id dependency reads session → returns company_id",
        "6. require_permission dependency checks user's roles → grants or returns 403",
        "7. require_module dependency checks company_settings.enabled_modules → 403 if not licensed",
        "8. Route handler calls service layer with validated data",
        "9. Service layer executes business logic via SQLAlchemy ORM",
        "10. Response serialized via Pydantic schema → returned as JSON",
    ]
    for step in steps:
        st.append(Paragraph(step, s["bullet"]))

    st.append(Paragraph("Deployment Architecture", s["h2"]))
    st.append(Paragraph(
        "The system is deployed as a Docker Compose stack with 4 services:",
        s["body"]))
    st.append(build_table(
        ["Service", "Image", "Port", "Role"],
        [
            ["db", "postgres:16-alpine", "5432 (internal)", "Primary database"],
            ["redis", "redis:7-alpine", "6379 (internal)", "Rate limiting + cache"],
            ["web", "custom (Python 3.12)", "8000 (internal)", "FastAPI backend"],
            ["frontend", "custom (Nginx 1.27)", "80 → 9009 (host)", "SPA + API proxy"],
        ],
        col_widths=[2.5 * cm, 3.5 * cm, 3.5 * cm, 7.5 * cm]
    ))
    st.append(PageBreak())

    # ── 3. Database Design ──
    st.append(Paragraph("3. Database Design", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "The database contains 40+ tables organized into functional domains. Every business table "
        "has a company_id foreign key for multi-tenant isolation. All foreign keys use ON DELETE CASCADE "
        "except AuthSession.current_company_id which uses SET NULL (to preserve session history).",
        s["body"]))

    st.append(Paragraph("Entity Relationship Overview", s["h2"]))
    st.append(build_table_left(
        ["Domain", "Tables", "Key Relationships"],
        [
            ["Auth", "users, auth_sessions", "auth_sessions.user_id → users.id"],
            ["Companies", "companies, branches, company_settings", "branches.company_id → companies.id"],
            ["RBAC", "roles, permissions, role_permissions, user_roles", "user_roles links users to companies with roles"],
            ["Partners", "partners", "partners.company_id → companies.id"],
            ["Items", "items, item_categories, units, unit_conversions", "items → categories, items → units"],
            ["Inventory", "warehouses, warehouse_stock, inventory_movements", "warehouse_stock → warehouses, items"],
            ["Sales", "sales_invoices, sales_invoice_lines", "lines.invoice_id → invoices.id (CASCADE)"],
            ["Purchases", "purchase_invoices, purchase_invoice_lines", "lines.invoice_id → invoices.id (CASCADE)"],
            ["Payments", "payments", "payments.partner_id → partners.id"],
            ["Accounting", "accounts, journal_entries, journal_lines", "journal_lines → entries, accounts"],
            ["Currencies", "currencies, currency_rates", "rates.company_id + currency_code → currencies"],
            ["HR", "departments, employees, attendance_records, payroll_runs, payroll_lines, leave_requests", "employees → departments"],
            ["Projects", "projects, project_cost_lines", "cost_lines.project_id → projects.id"],
            ["Manufacturing", "boms, bom_lines, work_orders, work_order_*", "BOMs define components, Work Orders consume them"],
            ["POS", "pos_sessions, pos_orders, pos_order_lines", "orders → sessions, lines → orders"],
            ["Infrastructure", "numbering_sequences", "Per-company sequential code generation"],
        ],
        col_widths=[2.5 * cm, 5 * cm, 9.5 * cm]
    ))

    st.append(Paragraph("Multi-Tenant Data Isolation", s["h2"]))
    st.append(Paragraph(
        "Every database query that touches business data is automatically filtered by company_id. "
        "This is enforced at the API layer through the get_current_company_id() FastAPI dependency, "
        "which reads the current_company_id from the user's auth session. The dependency returns "
        "HTTP 409 if no company is selected.",
        s["body"]))
    st.append(Paragraph(
        "The ORM models do not include company_id in query filters at the model level — isolation "
        "is purely at the API/service layer. This means direct database access (e.g., via psql) "
        "bypasses the isolation. For production deployments, database-level row security policies "
        "can be added as an additional layer of defense.",
        s["body"]))
    st.append(PageBreak())

    # ── 4. Modules Overview ──
    st.append(Paragraph("4. Modules Overview", s["h1"]))
    st.append(hr())

    modules_detail = [
        ("4.1 Sales Module", [
            ("Purpose", "Manage the complete sales lifecycle: create draft invoices, add line items with products and pricing, confirm invoices to trigger stock deduction and cost calculation, and delete draft invoices."),
            ("Key Models", "SalesInvoice (id, company_id, partner_id, number, date, currency_code, fx_rate, total_amount, total_amount_base, is_confirmed), SalesInvoiceLine (id, invoice_id, item_id, description, quantity, unit_price, line_total, cost_price, total_cost)"),
            ("Auto-Numbering", "Invoices are numbered per-company using sequential numbering (SI-0001, SI-0002, ...). The numbering uses SELECT ... FOR UPDATE to prevent race conditions."),
            ("Confirmation Logic", "On confirm: (1) validate all lines have items, (2) calculate total_amount and total_amount_base using fx_rate, (3) for each line: deduct quantity from warehouse_stock, record inventory_movement, calculate cost_price from average_cost, update line.total_cost."),
            ("Permissions", "sales.view (read), sales.manage (create/update/confirm), sales.delete (delete drafts only)"),
            ("Endpoints", "GET /sales-invoices, POST /sales-invoices, GET /sales-invoices/{id}, PATCH /sales-invoices/{id}, POST /sales-invoices/{id}/confirm, DELETE /sales-invoices/{id}"),
        ]),
        ("4.2 Purchases Module", [
            ("Purpose", "Manage the complete purchase lifecycle: create draft invoices, add line items with supplier pricing, confirm invoices to trigger stock-in and weighted-average cost recalculation."),
            ("Key Models", "PurchaseInvoice, PurchaseInvoiceLine — mirrors the Sales models with supplier-facing semantics."),
            ("Confirmation Logic", "On confirm: (1) validate lines, (2) calculate totals with FX, (3) for each line: add quantity to warehouse_stock, recalculate weighted_average_cost = (old_qty × old_avg + new_qty × unit_cost) / (old_qty + new_qty), record inventory_movement."),
            ("Cost Method", "Weighted Average Cost (WAC) is the default and only supported method. The average_cost field on warehouse_stock is updated atomically on each purchase confirmation."),
            ("Permissions", "purchases.view, purchases.manage, purchases.delete"),
        ]),
        ("4.3 Inventory Module", [
            ("Purpose", "Track stock levels across multiple warehouses, record all inventory movements, and support physical stock taking with adjustment posting."),
            ("Key Models", "Warehouse, WarehouseStock (per item per warehouse), InventoryMovement (every stock change is recorded here), StockTake, StockTakeLine."),
            ("Stock Balances", "warehouse_stock tracks current quantity and average_cost per item per warehouse. The total_value = quantity × average_cost."),
            ("Movements", "Every stock change creates an inventory_movement record with: item_id, warehouse_from_id, warehouse_to_id, quantity, movement_type (purchase_in, sale_out, manufacturing_in, manufacturing_out, transfer, adjustment), unit_cost, total_cost."),
            ("Stock Takes", "Physical counting workflow: (1) create stock take for a warehouse, (2) add items with book_qty (auto-fetched) and counted_qty, (3) system calculates diff_qty = counted - book, (4) on post: create adjustment movements and update warehouse_stock."),
            ("Permissions", "warehouses.view/manage/delete, stock.view, movements.view, stock_takes.view/manage"),
        ]),
        ("4.4 Accounting Module", [
            ("Purpose", "Full double-entry bookkeeping with chart of accounts, journal entries, and three financial reports."),
            ("Chart of Accounts", "Pre-seeded with 13 accounts covering: Cash, Accounts Receivable, Inventory, Fixed Assets, Accounts Payable, Sales Tax Payable, Salaries Payable, Owner's Equity, Sales Revenue, COGS, Operating Expenses, FX Gain, FX Loss. Companies can add custom accounts."),
            ("Journal Entries", "Double-entry: each entry has multiple journal_lines, each with debit or credit amount linked to an account. The system validates that total debits = total credits before posting."),
            ("Reports", "Trial Balance (all accounts with debit/credit totals), Income Statement (revenue - COGS - expenses = net income), Balance Sheet (assets = liabilities + equity). All reports are generated dynamically from journal_lines."),
            ("Permissions", "accounting.view, accounting.manage, accounting.reports"),
        ]),
        ("4.5 HR Module", [
            ("Purpose", "Manage employees, departments, attendance tracking, payroll processing, and leave requests."),
            ("Departments", "Organizational units. Each employee belongs to one department."),
            ("Employees", "Core employee record with: employee_number (auto-generated), name, position, department, hire_date, basic_salary, is_active."),
            ("Attendance", "Daily attendance recording per employee: present, absent, half_day, leave statuses. Used for payroll calculation."),
            ("Payroll", "Period-based payroll runs. On run: for each active employee, calculate basic_salary - deductions = net_salary. Records are created as PayrollLine records under a PayrollRun."),
            ("Leave Requests", "Workflow: employee submits request (type: annual/sick/unpaid, start_date, end_date, reason) → manager approves or rejects → status updated."),
            ("Permissions", "hr.view, hr.manage, hr.payroll"),
        ]),
        ("4.6 POS Module", [
            ("Purpose", "Session-based point of sale for retail operations with cash management."),
            ("Sessions", "Open session (record opening_cash) → process orders → close session (enter closing_cash, system calculates expected_cash and variance)."),
            ("Orders", "Each order is linked to a session, contains order_lines (item, quantity, unit_price), and generates a sales invoice on completion."),
            ("Permissions", "pos.view, pos.manage"),
        ]),
        ("4.7 Projects Module", [
            ("Purpose", "Track project profitability with cost allocation across materials, labor, and overhead."),
            ("Cost Lines", "Each project has multiple cost_lines categorized as material, labor, or overhead. Total cost is aggregated automatically."),
            ("Workflow", "Create project (with contract_value) → add cost lines throughout project life → mark complete → system calculates margin = contract_value - total_cost."),
            ("Permissions", "projects.view, projects.manage"),
        ]),
        ("4.8 Manufacturing Module", [
            ("Purpose", "Define bills of materials and execute work orders with full cost tracking."),
            ("BOMs", "Bill of Materials: defines the output product, output quantity, and required component items with quantities."),
            ("Work Orders", "Production execution: select BOM or product, planned quantity, link to warehouse. On finish: consume component materials from warehouse, add labor and overhead costs, add finished goods to warehouse."),
            ("Cost Allocation", "Work orders track: total_material_cost (from consumption), total_labor_cost (from labor lines), total_overhead_cost (from overhead lines), total_cost (sum of all three)."),
            ("Permissions", "manufacturing.view, manufacturing.manage"),
        ]),
    ]

    for title, items in modules_detail:
        st.append(Paragraph(title, s["h2"]))
        for field, desc in items:
            st.append(Paragraph(f"<b>{field}:</b>  {desc}", s["body"]))
        st.append(Spacer(1, 0.3 * cm))
    st.append(PageBreak())

    # ── 5. RBAC ──
    st.append(Paragraph("5. Role-Based Access Control (RBAC)", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "The RBAC system provides granular, per-company access control with 63 permission codes "
        "organized across all modules. Permissions follow the format: module.action.",
        s["body"]))

    st.append(Paragraph("Permission Tiers", s["h2"]))
    st.append(build_table(
        ["Tier", "Pattern", "Example", "Access Level"],
        [
            ["View", "<module>.view", "sales.view", "Read-only access to module data"],
            ["Manage", "<module>.manage", "sales.manage", "Create, update, confirm operations"],
            ["Delete", "<module>.delete", "sales.delete", "Permanent deletion (separate from manage)"],
            ["Reports", "<module>.reports", "accounting.reports", "Access to module-specific reports"],
            ["Special", "companies.delete_data", "—", "Danger zone: clear all company data"],
        ],
        col_widths=[2.5 * cm, 3 * cm, 4 * cm, 7.5 * cm]
    ))

    st.append(Paragraph("Permission Resolution", s["h2"]))
    st.append(Paragraph(
        "When a user makes an API request, the require_permission('code') dependency performs "
        "the following resolution:",
        s["body"]))
    res_steps = [
        "1. Extract user_id from the authenticated session",
        "2. Extract company_id from the session's current_company_id",
        "3. Query user_roles WHERE user_id = ? AND company_id = ?",
        "4. For each role, query role_permissions to get all permission_ids",
        "5. Union all permission codes across all roles",
        "6. Check if the required permission code exists in the union",
        "7. If found: proceed. If not: return HTTP 403 Forbidden",
    ]
    for step in res_steps:
        st.append(Paragraph(step, s["bullet"]))

    st.append(Paragraph("Role Management", s["h2"]))
    st.append(Paragraph(
        "Each company starts with a built-in 'Admin' role that automatically receives ALL 63 "
        "permissions. This role cannot be deleted or have its permissions reduced. Companies "
        "can create custom roles and assign specific permissions via the RBAC API or the "
        "Roles management page in the UI.",
        s["body"]))

    st.append(Paragraph("Complete Permission List", s["h2"]))
    all_perms = [
        ["partners.view / .manage / .delete", "Customer and supplier management"],
        ["categories.view / .manage / .delete", "Item category management"],
        ["units.view / .manage / .delete", "Unit of measure management"],
        ["unit_conversions.view / .manage / .delete", "Unit conversion rules"],
        ["items.view / .manage / .delete", "Product and service management"],
        ["warehouses.view / .manage / .delete", "Warehouse management"],
        ["stock.view", "View stock balances"],
        ["movements.view", "View inventory movements"],
        ["stock_takes.view / .manage", "Physical stock counting"],
        ["sales.view / .manage / .delete", "Sales invoice operations"],
        ["purchases.view / .manage / .delete", "Purchase invoice operations"],
        ["payments.view / .manage", "Payment recording"],
        ["currencies.view / .manage / .delete", "Currency management"],
        ["currency_rates.view / .manage / .delete", "Exchange rate management"],
        ["accounting.view / .manage / .reports", "Chart of accounts, journals, reports"],
        ["hr.view / .manage / .payroll", "HR and payroll operations"],
        ["projects.view / .manage", "Project management"],
        ["manufacturing.view / .manage", "BOM and work order management"],
        ["pos.view / .manage", "Point of sale operations"],
        ["companies.view / .manage", "Company settings"],
        ["companies.delete_data", "Danger zone: clear all operational data"],
        ["roles.view / .manage", "Role and permission management"],
        ["users.view / .manage", "Company user management"],
    ]
    st.append(build_table_left(
        ["Permission Codes", "Description"],
        all_perms,
        col_widths=[6 * cm, 11 * cm]
    ))
    st.append(PageBreak())

    # ── 6. Security Model ──
    st.append(Paragraph("6. Security Model", s["h1"]))
    st.append(hr())

    security_items = [
        ("6.1 Authentication",
         "The system uses opaque bearer tokens (not JWT). On login, a cryptographically random "
         "token is generated using secrets.token_urlsafe(32). Only the SHA-256 hash of the token "
         "is stored in the auth_sessions table. The raw token is returned to the client once and "
         "never stored server-side. Tokens expire after ACCESS_TOKEN_EXPIRE_MINUTES (default: 1440 = 24 hours). "
         "Sessions can be revoked via the logout endpoint."),
        ("6.2 Rate Limiting",
         "Redis-backed rate limiting protects the login endpoint. Per (IP + email): 5 max attempts "
         "in a 15-minute window with 5-minute lockout. Per IP (distributed spray protection): 20 max "
         "attempts in 15 minutes. The system fails open — if Redis is unreachable, login proceeds without "
         "rate limiting. Counters are cleared on successful login."),
        ("6.3 Password Policy",
         "Minimum 8 characters. Strength scoring based on: length (2+ chars=1pt, 8+=1pt), lowercase "
         "(1pt), uppercase (1pt), digit (1pt), symbol (1pt). Minimum score: 3/5. Passwords are hashed "
         "using bcrypt with automatic salting."),
        ("6.4 CORS Protection",
         "Configurable via CORS_ORIGINS environment variable. Defaults to same-origin (empty string). "
         "In production with a single origin (Nginx proxy), no CORS configuration is needed."),
        ("6.5 Security Headers",
         "The Nginx configuration serves the following security headers: Content-Security-Policy "
         "(default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'), X-Frame-Options: DENY, "
         "X-Content-Type-Options: nosniff, X-XSS-Protection: 1; mode=block, Referrer-Policy: strict-origin, "
         "Permissions-Policy: camera=(), microphone=(), geolocation=()"),
        ("6.6 Data Isolation",
         "Every business query is filtered by company_id at the API layer. Users can only access "
         "data for companies they have a role in. The get_current_company_id dependency enforces this "
         "on every endpoint that touches business data. Direct database access bypasses this — for "
         "production, consider PostgreSQL Row-Level Security policies."),
    ]
    for title, desc in security_items:
        st.append(Paragraph(title, s["h2"]))
        st.append(Paragraph(desc, s["body"]))
    st.append(PageBreak())

    # ── 7. Competitive Analysis ──
    st.append(Paragraph("7. Competitive Analysis", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "ERP Pro is positioned in the market as a self-hosted, bilingual ERP system targeting "
        "small and medium businesses. The following comparison highlights key differentiators:",
        s["body"]))

    st.append(build_table(
        ["Feature", "ERP Pro", "Odoo", "ERPNext", "Rushd", "Zoho"],
        [
            ["Hosting", "Self-hosted", "Cloud/Hosted", "Cloud/Hosted", "Cloud only", "Cloud only"],
            ["Price", "FREE (self-host)", "$20-40/user/mo", "$50/tenant/mo", "2-5K EGP/mo", "$15-60/user/mo"],
            ["Source Code", "Full access", "Enterprise only", "Open source", "Proprietary", "Proprietary"],
            ["Languages", "EN + AR (RTL)", "Multi-lang", "Multi-lang", "AR only", "EN mainly"],
            ["RBAC Granularity", "63 codes (VMD)", "Group-based", "Role-based", "Basic roles", "Role-based"],
            ["Module Licensing", "Per-company", "Per-user", "All-included", "Tiered", "Per-user"],
            ["POS Built-in", "Yes (session)", "Yes (complex)", "Yes (basic)", "Basic", "No"],
            ["Manufacturing", "Yes (BOM+WO)", "Yes (advanced)", "Yes (basic)", "No", "No"],
            ["Deployment", "Docker one-cmd", "Complex", "Docker/bench", "Cloud only", "Cloud only"],
            ["API Docs", "Auto (Swagger)", "Auto (Swagger)", "Auto (Swagger)", "Limited", "REST only"],
            ["Tests", "110+ unit + 24 E2E", "Extensive", "Extensive", "Unknown", "Unknown"],
        ],
        col_widths=[3 * cm, 3 * cm, 3 * cm, 3 * cm, 2.5 * cm, 2.5 * cm]
    ))

    st.append(Paragraph("Key Differentiators", s["h2"]))
    diffs = [
        "True bilingual AR/EN with proper RTL layout — not an afterthought or plugin",
        "Self-hosted with full source code — complete data sovereignty, no vendor lock-in",
        "Granular view/manage/delete permissions per module — not just role-level",
        "Module licensing — companies only pay for and see the modules they use",
        "Docker one-command deployment — identical behavior on laptop and production server",
        "Weighted-average costing built-in — recalculated automatically on each purchase",
        "Auto-numbering with row-level locking — prevents duplicate invoice numbers under concurrency",
        "Platform admin panel — manage all tenants from a single superuser dashboard",
        "110 automated tests + 24 E2E browser tests — verified reliability",
        "Low-stock email alerts with configurable thresholds per item and per company",
    ]
    for d in diffs:
        st.append(Paragraph(f"✓  {d}", s["bullet"]))
    st.append(PageBreak())

    # ── 8. API Reference ──
    st.append(Paragraph("8. Complete API Reference", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "All endpoints are prefixed with /api/v1. Authentication is via Bearer token in the "
        "Authorization header. The complete interactive API documentation is available at "
        "/api/v1/docs (Swagger UI) when the server is running.",
        s["body"]))

    api_rows = [
        ["Auth", "POST", "/auth/login", "None", "Rate-limited login"],
        ["Auth", "POST", "/auth/logout", "Bearer", "Revoke session"],
        ["Auth", "POST", "/auth/select-company", "Bearer", "Set active company/branch"],
        ["Auth", "GET", "/auth/me", "Bearer", "User info + permissions"],
        ["Companies", "GET", "/companies", "companies.view", "List user's companies"],
        ["Companies", "GET", "/companies/current", "companies.view", "Current company details"],
        ["Companies", "GET", "/companies/settings", "companies.view", "Company settings"],
        ["Companies", "PATCH", "/companies/settings", "companies.manage", "Update settings"],
        ["Companies", "POST", "/companies/{id}/branches", "companies.manage", "Create branch"],
        ["Companies", "POST", "/companies/current/danger/clear-data", "companies.delete_data", "Clear operational data"],
        ["RBAC", "GET", "/permissions", "roles.view", "List all permission codes"],
        ["RBAC", "GET", "/roles", "roles.view", "List company roles"],
        ["RBAC", "POST", "/roles", "roles.manage", "Create role"],
        ["RBAC", "PATCH", "/roles/{id}/permissions", "roles.manage", "Update role permissions"],
        ["RBAC", "DELETE", "/roles/{id}", "roles.manage", "Delete role (must be empty)"],
        ["RBAC", "GET", "/company-users", "users.view", "List company users"],
        ["RBAC", "POST", "/company-users", "users.manage", "Create company user"],
        ["RBAC", "PATCH", "/company-users/{id}/roles", "users.manage", "Update user roles"],
        ["RBAC", "PATCH", "/company-users/{id}/status", "users.manage", "Activate/deactivate"],
        ["Platform", "GET", "/platform/modules", "superuser", "List sellable modules"],
        ["Platform", "GET", "/platform/companies", "superuser", "List all tenants"],
        ["Platform", "POST", "/platform/companies", "superuser", "Create tenant"],
        ["Platform", "GET", "/platform/companies/{id}", "superuser", "Tenant details"],
        ["Platform", "PATCH", "/platform/companies/{id}", "superuser", "Update tenant"],
        ["Platform", "DELETE", "/platform/companies/{id}", "superuser", "Delete tenant (cascades)"],
        ["Partners", "GET", "/partners", "partners.view", "List partners"],
        ["Partners", "POST", "/partners", "partners.manage", "Create partner"],
        ["Partners", "GET", "/partners/{id}", "partners.view", "Partner details"],
        ["Partners", "PATCH", "/partners/{id}", "partners.manage", "Update partner"],
        ["Partners", "DELETE", "/partners/{id}", "partners.delete", "Delete partner"],
        ["Items", "GET", "/items", "items.view", "List items"],
        ["Items", "POST", "/items", "items.manage", "Create item"],
        ["Items", "PATCH", "/items/{id}", "items.manage", "Update item"],
        ["Items", "DELETE", "/items/{id}", "items.delete", "Delete item"],
        ["Categories", "GET", "/item-categories", "categories.view", "List categories"],
        ["Categories", "POST", "/item-categories", "categories.manage", "Create category"],
        ["Units", "GET", "/units", "units.view", "List units"],
        ["Units", "POST", "/units", "units.manage", "Create unit"],
        ["Warehouses", "GET", "/warehouses", "warehouses.view", "List warehouses"],
        ["Warehouses", "POST", "/warehouses", "warehouses.manage", "Create warehouse"],
        ["Stock", "GET", "/warehouse-stock", "stock.view", "Stock balances"],
        ["Movements", "GET", "/inventory-movements", "movements.view", "Movement history"],
        ["Stock Takes", "GET", "/stock-takes", "stock_takes.view", "List stock takes"],
        ["Stock Takes", "POST", "/stock-takes", "stock_takes.manage", "Create stock take"],
        ["Stock Takes", "POST", "/stock-takes/{id}/post", "stock_takes.manage", "Post adjustments"],
        ["Sales", "GET", "/sales-invoices", "sales.view", "List sales invoices"],
        ["Sales", "POST", "/sales-invoices", "sales.manage", "Create sales invoice"],
        ["Sales", "PATCH", "/sales-invoices/{id}", "sales.manage", "Update invoice"],
        ["Sales", "POST", "/sales-invoices/{id}/confirm", "sales.manage", "Confirm (stock-out)"],
        ["Sales", "DELETE", "/sales-invoices/{id}", "sales.delete", "Delete draft"],
        ["Purchases", "GET", "/purchase-invoices", "purchases.view", "List purchase invoices"],
        ["Purchases", "POST", "/purchase-invoices", "purchases.manage", "Create purchase invoice"],
        ["Purchases", "POST", "/purchase-invoices/{id}/confirm", "purchases.manage", "Confirm (stock-in + cost update)"],
        ["Payments", "GET", "/payments", "payments.view", "List payments"],
        ["Payments", "POST", "/payments", "payments.manage", "Create payment"],
        ["Currencies", "GET", "/currencies", "currencies.view", "List currencies"],
        ["Currencies", "POST", "/currencies", "currencies.manage", "Create currency"],
        ["FX Rates", "GET", "/currency-rates", "currency_rates.view", "List exchange rates"],
        ["FX Rates", "POST", "/currency-rates", "currency_rates.manage", "Create exchange rate"],
        ["Accounts", "GET", "/accounting/accounts", "accounting.view", "Chart of accounts"],
        ["Accounts", "POST", "/accounting/accounts", "accounting.manage", "Create account"],
        ["Journals", "GET", "/accounting/journal-entries", "accounting.view", "List journal entries"],
        ["Journals", "POST", "/accounting/journal-entries", "accounting.manage", "Create entry"],
        ["Reports", "GET", "/accounting/reports/trial-balance", "accounting.reports", "Trial balance"],
        ["Reports", "GET", "/accounting/reports/income-statement", "accounting.reports", "Income statement"],
        ["Reports", "GET", "/accounting/reports/balance-sheet", "accounting.reports", "Balance sheet"],
        ["HR", "GET", "/hr/departments", "hr.view", "List departments"],
        ["HR", "POST", "/hr/departments", "hr.manage", "Create department"],
        ["HR", "GET", "/hr/employees", "hr.view", "List employees"],
        ["HR", "POST", "/hr/employees", "hr.manage", "Create employee"],
        ["HR", "POST", "/hr/attendance", "hr.manage", "Record attendance"],
        ["HR", "POST", "/hr/payroll/run", "hr.payroll", "Run payroll"],
        ["HR", "GET", "/hr/leave-requests", "hr.view", "List leave requests"],
        ["HR", "POST", "/hr/leave-requests", "hr.manage", "Create leave request"],
        ["HR", "POST", "/hr/leave-requests/{id}/status", "hr.manage", "Approve/reject"],
        ["Projects", "GET", "/projects/", "projects.view", "List projects"],
        ["Projects", "POST", "/projects/", "projects.manage", "Create project"],
        ["Projects", "POST", "/projects/{id}/costs", "projects.manage", "Add cost line"],
        ["Projects", "POST", "/projects/{id}/complete", "projects.manage", "Mark complete"],
        ["Mfg", "GET", "/manufacturing/boms", "manufacturing.view", "List BOMs"],
        ["Mfg", "POST", "/manufacturing/boms", "manufacturing.manage", "Create BOM"],
        ["Mfg", "GET", "/manufacturing/work-orders", "manufacturing.view", "List work orders"],
        ["Mfg", "POST", "/manufacturing/work-orders", "manufacturing.manage", "Create work order"],
        ["Mfg", "POST", "/manufacturing/work-orders/{id}/finish", "manufacturing.manage", "Finish (stock-in)"],
        ["POS", "GET", "/pos/sessions", "pos.view", "List POS sessions"],
        ["POS", "POST", "/pos/sessions", "pos.manage", "Open session"],
        ["POS", "POST", "/pos/sessions/{id}/close", "pos.manage", "Close session"],
        ["POS", "GET", "/pos/orders", "pos.view", "List POS orders"],
        ["POS", "POST", "/pos/orders", "pos.manage", "Create POS order"],
        ["Reports", "GET", "/reports/sales-summary", "accounting.reports", "Sales summary"],
        ["Reports", "GET", "/reports/stock-value", "stock_takes.view", "Stock value report"],
        ["Reports", "GET", "/reports/low-stock", "stock_takes.view", "Low stock items"],
        ["Reports", "GET", "/reports/project-costs", "projects.view", "Project cost report"],
    ]
    st.append(build_table(
        ["Module", "Method", "Endpoint", "Permission", "Description"],
        api_rows,
        col_widths=[2 * cm, 1.5 * cm, 5 * cm, 4 * cm, 4.5 * cm]
    ))

    doc.build(st, onFirstPage=page_number, onLaterPages=page_number)
    print(f"  ✓ {os.path.basename(path)}")


# ===========================================================================
# PDF 2 — Feasibility Study & Pricing
# ===========================================================================

def build_pdf2(path):
    doc = make_doc(path, "ERP Pro — Feasibility Study & Pricing")
    s = S()
    st = []

    # Cover
    st.append(Spacer(1, 6 * cm))
    st.append(Paragraph("Feasibility Study & Pricing", s["cover_title"]))
    st.append(Paragraph("Egyptian Market Analysis", s["cover_sub"]))
    st.append(Spacer(1, 1 * cm))
    st.append(Paragraph("Version 1.0  •  August 2026", s["cover_version"]))
    st.append(PageBreak())

    # 1. Executive Summary
    st.append(Paragraph("1. Executive Summary", s["h1"]))
    st.append(hr())
    st.append(Paragraph(
        "ERP Pro is an open-source, self-hosted Enterprise Resource Planning system designed "
        "for Egyptian small and medium enterprises (SMEs). This document presents a feasibility "
        "study and pricing strategy for launching ERP Pro as a SaaS platform targeting the "
        "Egyptian market, where ERP adoption among SMEs is estimated at less than 5%.",
        s["body"]))
    st.append(Paragraph(
        "The system addresses a clear market gap: no existing bilingual (Arabic/English) ERP "
        "system with professional UI, granular RBAC, modular licensing, and self-hosting capability "
        "is available at an affordable price point for Egyptian businesses. Competitors like Odoo "
        "($20-40/user/month), ERPNext ($50/tenant/month), and Rushd (2,000-5,000 EGP/month) either "
        "lack Arabic support, are prohibitively expensive, or offer limited customization.",
        s["body"]))

    st.append(Paragraph("Investment Summary", s["h2"]))
    st.append(build_table(
        ["Metric", "Value"],
        [
            ["Initial Development Cost", "520,000 EGP (one-time)"],
            ["Monthly Operating Cost", "1,600 - 2,900 EGP"],
            ["Break-even Point", "~40 paying customers (Month 10-12)"],
            ["Year 1 Revenue Projection", "504,000 EGP (ARR at Month 12)"],
            ["Year 3 Revenue Projection", "3,360,000 EGP (ARR at Month 36)"],
            ["Target Customer Count (Year 3)", "200 paying companies"],
            ["Average Revenue Per Customer", "1,400 EGP/month"],
        ],
        col_widths=[6 * cm, 11 * cm]
    ))
    st.append(PageBreak())

    # 2. Market Analysis
    st.append(Paragraph("2. Market Analysis", s["h1"]))
    st.append(hr())

    st.append(Paragraph("2.1 Target Market Size", s["h2"]))
    st.append(Paragraph(
        "Egypt has over 2.5 million active registered businesses according to the General "
        "Authority for Investment and Free Zones. The vast majority are SMEs with 5-50 employees. "
        "Key market segments include:",
        s["body"]))
    segments = [
        ("Micro Enterprises (1-5 employees)", "~1.8 million businesses, primarily shops, small "
         "traders, and service providers. Price-sensitive, need simple accounting and inventory."),
        ("Small Enterprises (6-25 employees)", "~500,000 businesses, growing companies with "
         "multiple departments. Need integrated sales, purchases, inventory, and basic accounting."),
        ("Medium Enterprises (26-250 employees)", "~200,000 businesses, established companies "
         "with complex operations. Need full ERP including HR, manufacturing, and project management."),
    ]
    for title, desc in segments:
        st.append(Paragraph(f"<b>{title}:</b>  {desc}", s["body"]))

    st.append(Paragraph("2.2 Market Gap Analysis", s["h2"]))
    st.append(Paragraph(
        "Current ERP solutions in the Egyptian market have significant gaps that ERP Pro addresses:",
        s["body"]))
    st.append(build_table(
        ["Gap", "Current State", "ERP Pro Solution"],
        [
            ["Language", "Most systems are EN-only or AR-only", "True bilingual with RTL support"],
            ["Cost", "2,000-15,000 EGP/month for existing solutions", "Free self-hosted, 499+ EGP SaaS"],
            ["Deployment", "Complex setup, requires IT expertise", "Docker one-command deployment"],
            ["Data Sovereignty", "Cloud-only, data on foreign servers", "Self-hosted, full data control"],
            ["Customization", "Proprietary, limited modification", "Full source code access"],
            ["Modularity", "Pay for all modules or none", "Enable only what you use"],
            ["Arabic UI", "Poor RTL, untranslated interfaces", "Native Arabic design"],
        ],
        col_widths=[3 * cm, 6.5 * cm, 7.5 * cm]
    ))

    st.append(Paragraph("2.3 Competitive Landscape", s["h2"]))
    st.append(build_table(
        ["System", "Hosting", "Price (Monthly)", "Language", "Market Share (Egypt)"],
        [
            ["Odoo", "Cloud/Self-hosted", "$20-40/user/mo", "Multi-lang", "Growing (5-10%)"],
            ["ERPNext", "Cloud/Self-hosted", "$50/tenant/mo", "Multi-lang", "Niche (1-2%)"],
            ["Rushd", "Cloud only", "2,000-5,000 EGP/mo", "AR only", "Established (10-15%)"],
            ["Zoho", "Cloud only", "$15-60/user/mo", "EN mainly", "Small (3-5%)"],
            ["QuickBooks", "Cloud only", "$30-200/mo", "EN only", "Accounting only (5%)"],
            ["ERP Pro", "Self-hosted", "Free / 499+ EGP", "EN + AR", "New entrant"],
        ],
        col_widths=[2.5 * cm, 3 * cm, 3.5 * cm, 3 * cm, 5 * cm]
    ))
    st.append(PageBreak())

    # 3. Pricing Model
    st.append(Paragraph("3. Pricing Model", s["h1"]))
    st.append(hr())

    st.append(Paragraph("3.1 SaaS Subscription Tiers", s["h2"]))
    st.append(Paragraph(
        "The pricing is designed to be accessible to Egyptian SMEs while covering operating costs "
        "and generating sustainable revenue. All prices are in Egyptian Pounds (EGP).",
        s["body"]))
    st.append(build_table(
        ["Plan", "Price/Month", "Users", "Modules", "Storage", "Support"],
        [
            ["Starter", "499 EGP", "2", "Sales, Purchases,\nInventory", "1 GB", "Email only"],
            ["Business", "1,499 EGP", "5", "All 8 modules", "5 GB", "Email + Chat"],
            ["Enterprise", "3,499 EGP", "20", "All modules", "20 GB", "Priority support"],
            ["Custom", "Contact us", "Unlimited", "Custom config", "Unlimited", "Dedicated manager"],
        ],
        col_widths=[2.2 * cm, 2.5 * cm, 1.8 * cm, 3.5 * cm, 2 * cm, 3 * cm]
    ))

    st.append(Paragraph("3.2 Pricing Justification", s["h2"]))
    st.append(Paragraph(
        "The Starter plan at 499 EGP/month is positioned below the cheapest competitor (Rushd at "
        "2,000 EGP/month) while providing core functionality. The Business plan at 1,499 EGP/month "
        "offers all modules at a fraction of Odoo's per-user pricing. For a 5-person team, Odoo "
        "would cost 100-200 USD (3,500-7,000 EGP/month) vs ERP Pro's 1,499 EGP.",
        s["body"]))

    st.append(Paragraph("3.3 Additional Revenue Streams", s["h2"]))
    rev = [
        ("Annual Discount", "20% off for annual prepayment (pay 10 months, get 12). Encourages commitment and improves cash flow."),
        ("Onboarding Service", "Free for Business+ plans. 2,000 EGP one-time for Starter plan. Includes data import, configuration, and training."),
        ("Custom Module Development", "Quote-based pricing for custom module development. Typical range: 20,000-100,000 EGP per module."),
        ("Premium Support SLA", "1,500 EGP/month for guaranteed 4-hour response time and dedicated support channel."),
        ("Training Sessions", "500 EGP per 2-hour session. On-site or remote. Covers system administration, module-specific training, or advanced accounting."),
        ("Data Migration", "Quote-based pricing for migrating data from other systems (Odoo, Excel, Rushd, etc.)."),
    ]
    for title, desc in rev:
        st.append(Paragraph(f"<b>{title}:</b>  {desc}", s["body"]))

    st.append(Paragraph("3.4 Free Trial Strategy", s["h2"]))
    st.append(Paragraph(
        "14-day free trial with full Business plan features. No credit card required. "
        "Trial instances are automatically deleted after 30 days if not converted. "
        "This reduces friction for evaluation while controlling infrastructure costs.",
        s["body"]))
    st.append(PageBreak())

    # 4. Development Costs
    st.append(Paragraph("4. Development Costs", s["h1"]))
    st.append(hr())

    st.append(Paragraph("4.1 One-Time Development Investment", s["h2"]))
    st.append(build_table(
        ["Category", "Cost (EGP)", "Breakdown"],
        [
            ["Backend Development", "200,000", "API design, business logic, database, testing"],
            ["Frontend Development", "150,000", "React UI, all pages, responsive design, RTL"],
            ["DevOps & Infrastructure", "50,000", "Docker setup, CI/CD, monitoring, deployment"],
            ["QA & Testing", "50,000", "Unit tests (110), E2E tests (24), manual testing"],
            ["Documentation", "30,000", "Technical docs, user manual, API docs, PDFs"],
            ["UI/UX Design", "40,000", "Wireframes, mockups, design system, dark mode"],
            ["Total", "520,000", "One-time investment"],
        ],
        col_widths=[4 * cm, 3 * cm, 10 * cm]
    ))

    st.append(Paragraph("4.2 Monthly Operating Costs (Cloud Deployment)", s["h2"]))
    st.append(Paragraph(
        "These costs assume a single-server deployment handling up to 100 tenant companies:",
        s["body"]))
    st.append(build_table(
        ["Item", "Specification", "Monthly Cost (EGP)"],
        [
            ["VPS Server", "4 vCPU, 8GB RAM, 100GB SSD (DigitalOcean/Hetzner)", "800 - 1,200"],
            ["PostgreSQL", "Managed database or self-hosted on same VPS", "0 - 500"],
            ["Redis", "Included with most VPS providers", "0"],
            ["Domain + SSL", "1 domain + free Let's Encrypt SSL", "50 - 100"],
            ["Backup Storage", "S3-compatible object storage, 50GB", "100 - 200"],
            ["Email Service", "Transactional email (SMTP relay or SendGrid free tier)", "0 - 100"],
            ["Monitoring", "Uptime monitoring (UptimeRobot free tier)", "0"],
            ["Total", "", "950 - 2,100"],
        ],
        col_widths=[3 * cm, 8 * cm, 4 * cm]
    ))

    st.append(Paragraph("4.3 Scaling Cost Projections", s["h2"]))
    st.append(build_table(
        ["Scale", "Customers", "Server Spec", "Monthly Cost (EGP)"],
        [
            ["Launch", "1-50", "4 vCPU, 8GB RAM", "1,500"],
            ["Growth", "50-200", "8 vCPU, 16GB RAM", "3,000"],
            ["Scale", "200-500", "16 vCPU, 32GB RAM + read replica", "6,000"],
            ["Enterprise", "500+", "Kubernetes cluster + managed DB", "15,000+"],
        ],
        col_widths=[2.5 * cm, 3 * cm, 5.5 * cm, 4 * cm]
    ))
    st.append(PageBreak())

    # 5. Financial Projections
    st.append(Paragraph("5. Financial Projections", s["h1"]))
    st.append(hr())

    st.append(Paragraph("5.1 Revenue Projections (36-Month)", s["h2"]))
    st.append(build_table(
        ["Month", "Customers", "Plan Mix", "MRR (EGP)", "ARR (EGP)", "Cumulative Revenue"],
        [
            ["3", "5", "3 Starter + 2 Biz", "4,500", "54,000", "13,500"],
            ["6", "15", "8 Starter + 5 Biz + 2 Ent", "19,500", "234,000", "72,000"],
            ["9", "25", "12 Starter + 8 Biz + 5 Ent", "33,500", "402,000", "189,000"],
            ["12", "40", "18 Starter + 14 Biz + 8 Ent", "56,000", "672,000", "378,000"],
            ["18", "70", "28 Starter + 25 Biz + 17 Ent", "98,000", "1,176,000", "882,000"],
            ["24", "120", "45 Starter + 42 Biz + 33 Ent", "168,000", "2,016,000", "1,890,000"],
            ["36", "200", "70 Starter + 70 Biz + 60 Ent", "280,000", "3,360,000", "5,040,000"],
        ],
        col_widths=[1.5 * cm, 2 * cm, 4 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm]
    ))

    st.append(Paragraph("5.2 Break-Even Analysis", s["h2"]))
    st.append(Paragraph(
        "Fixed monthly costs: ~2,000 EGP (server + infrastructure). Variable costs per customer: ~0 EGP "
        "(shared infrastructure). Average revenue per customer: ~1,400 EGP/month (blended across plans).",
        s["body"]))
    st.append(Paragraph(
        "Break-even formula: Customers_needed = Monthly_Fixed_Costs / Avg_Revenue_Per_Customer = "
        "2,000 / 1,400 = ~1.5 customers. However, the initial 520,000 EGP development investment "
        "must also be recovered. Payback period: 520,000 / (56,000 - 2,000) = ~10 months at Month 12 "
        "run rate. Full payback expected at Month 10-12.",
        s["body"]))

    st.append(Paragraph("5.3 Profitability Timeline", s["h2"]))
    st.append(build_table(
        ["Period", "Revenue", "Costs", "Net Profit", "Status"],
        [
            ["Month 1-3", "13,500", "526,000", "-512,500", "Investment phase"],
            ["Month 4-6", "58,500", "6,000", "+52,500", "Monthly profitable"],
            ["Month 7-12", "306,000", "12,000", "+294,000", "Recovering investment"],
            ["Year 1 Total", "378,000", "532,000", "-154,000", "Net: recovering"],
            ["Year 2 Total", "1,512,000", "24,000", "+1,488,000", "Fully profitable"],
            ["Year 3 Total", "3,150,000", "36,000", "+3,114,000", "Strong growth"],
        ],
        col_widths=[3 * cm, 3 * cm, 3 * cm, 3 * cm, 5 * cm]
    ))
    st.append(PageBreak())

    # 6. Risks
    st.append(Paragraph("6. Risks & Mitigations", s["h1"]))
    st.append(hr())

    st.append(build_table_left(
        ["Risk", "Severity", "Probability", "Mitigation Strategy"],
        [
            ["Low market adoption", "High", "Medium",
             "Free trial, onboarding support, Arabic-first marketing, partnership with local accountants"],
            ["Competition from Odoo", "High", "High",
             "Focus on Arabic UX, self-hosted option, lower price point, faster deployment"],
            ["Data security breach", "Critical", "Low",
             "Self-hosted = data sovereignty, security headers, rate limiting, regular security audits"],
            ["Currency fluctuation (EGP)", "Medium", "High",
             "EGP-denominated pricing, quarterly price reviews, USD cost hedging"],
            ["Talent acquisition", "Medium", "Medium",
             "Remote-friendly, competitive salaries, open-source community building"],
            ["Scaling limitations", "Low", "Low",
             "PostgreSQL handles millions of rows, horizontal scaling with read replicas"],
            ["Regulatory changes", "Medium", "Low",
             "Modular architecture allows quick compliance updates, tax module extensibility"],
            ["Server infrastructure failure", "High", "Low",
             "Automated daily backups, 14-day retention, tested restore procedure"],
        ],
        col_widths=[3.5 * cm, 2 * cm, 2 * cm, 9.5 * cm]
    ))

    st.append(Paragraph("6.1 Contingency Plans", s["h2"]))
    contingency = [
        "If adoption is slower than projected: reduce marketing spend, focus on organic growth through open-source community, offer extended free trials.",
        "If a major competitor launches Arabic support: accelerate feature development, differentiate on self-hosting and data sovereignty.",
        "If EGP devalues significantly: switch to USD-denominated pricing for international customers, adjust EGP prices quarterly.",
        "If infrastructure costs spike: migrate to bare-metal servers, optimize database queries, implement aggressive caching.",
    ]
    for c in contingency:
        st.append(Paragraph(f"•  {c}", s["bullet"]))
    st.append(PageBreak())

    # 7. Implementation Roadmap
    st.append(Paragraph("7. Implementation Roadmap", s["h1"]))
    st.append(hr())

    st.append(build_table(
        ["Phase", "Timeline", "Deliverables", "Budget (EGP)"],
        [
            ["MVP Launch", "Month 1-2", "Core modules, Docker deployment, basic docs", "100,000"],
            ["SaaS Platform", "Month 3-4", "Multi-tenant hosting, billing, SuperAdmin panel", "150,000"],
            ["Market Entry", "Month 5-6", "Marketing site, free trial, onboarding flow", "100,000"],
            ["Growth", "Month 7-12", "Feature additions, mobile app, integrations", "170,000"],
            ["Scale", "Year 2", "Enterprise features, API marketplace, partnerships", "200,000"],
        ],
        col_widths=[3 * cm, 3 * cm, 7 * cm, 3 * cm]
    ))

    doc.build(st, onFirstPage=page_number, onLaterPages=page_number)
    print(f"  ✓ {os.path.basename(path)}")


# ===========================================================================
# PDF 3 — Deployment Guide
# ===========================================================================

def build_pdf3(path):
    doc = make_doc(path, "ERP Pro — Deployment Guide")
    s = S()
    st = []

    # Cover
    st.append(Spacer(1, 6 * cm))
    st.append(Paragraph("Deployment Guide", s["cover_title"]))
    st.append(Paragraph("Local Setup  •  Cloud Deployment  •  Security  •  Multi-Tenant", s["cover_sub"]))
    st.append(Spacer(1, 1 * cm))
    st.append(Paragraph("Version 1.0  •  August 2026", s["cover_version"]))
    st.append(PageBreak())

    # TOC
    st.append(Paragraph("Table of Contents", s["h1"]))
    st.append(hr())
    for item in [
        "1. Local Development Setup",
        "2. Production Server Deployment",
        "3. Domain & SSL Configuration",
        "4. Multi-Tenant Architecture",
        "5. Adding New Companies",
        "6. Security Hardening",
        "7. Backup & Disaster Recovery",
        "8. Monitoring & Maintenance",
        "9. Troubleshooting",
    ]:
        st.append(Paragraph(item, s["toc"]))
    st.append(PageBreak())

    # 1. Local Setup
    st.append(Paragraph("1. Local Development Setup", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Prerequisites", s["h2"]))
    st.append(build_table(
        ["Requirement", "Minimum", "Recommended"],
        [
            ["Docker Desktop", "4.0+", "4.20+ with Compose v2"],
            ["RAM", "4 GB", "8 GB"],
            ["Disk Space", "10 GB free", "20 GB free"],
            ["OS", "Windows 10+, macOS 12+, Ubuntu 20+", "Windows 11, Ubuntu 22.04"],
        ],
        col_widths=[4 * cm, 5 * cm, 8 * cm]
    ))

    st.append(Paragraph("Windows Quick Start", s["h2"]))
    st.append(Paragraph(
        "<b>Step 1:</b> Double-click <b>setup.bat</b> (one-time only). This script:", s["body"]))
    for item in [
        "Opens Docker Desktop if not running",
        "Creates .env file with random SECRET_KEY and POSTGRES_PASSWORD",
        "Builds Docker images for all 4 services",
        "Installs Python test requirements",
        "Runs the full test suite (110 tests) to verify the setup",
    ]:
        st.append(Paragraph(f"  →  {item}", s["sub_bullet"]))

    st.append(Paragraph(
        "<b>Step 2:</b> Double-click <b>start.bat</b>. This script:", s["body"]))
    for item in [
        "Starts Docker Compose (db, redis, web, frontend)",
        "Waits for PostgreSQL to be healthy",
        "Runs Alembic migrations to create/update tables",
        "Seeds demo data (company, admin user, sample items)",
        "Opens browser to http://localhost:9009/",
    ]:
        st.append(Paragraph(f"  →  {item}", s["sub_bullet"]))

    st.append(Paragraph("Linux / Any Server", s["h2"]))
    st.append(Paragraph(
        "One command does everything:", s["body"]))
    st.append(Paragraph("./start.sh", s["code"]))
    st.append(Paragraph(
        "The start.sh script is idempotent — safe to run multiple times. It creates .env on first "
        "run, builds images, starts services, runs migrations, and seeds data.",
        s["body"]))

    st.append(Paragraph("Manual Steps (if needed)", s["h2"]))
    st.append(Paragraph(
        "# Build and start all services<br/>"
        "docker compose up --build -d<br/><br/>"
        "# Watch logs<br/>"
        "docker compose logs -f web<br/><br/>"
        "# Run migrations manually<br/>"
        "docker compose exec -T web alembic upgrade head<br/><br/>"
        "# Seed demo data<br/>"
        "docker compose exec -T web python -m scripts.seed<br/><br/>"
        "# Stop services (keeps data)<br/>"
        "docker compose down<br/><br/>"
        "# Stop and DELETE all data<br/>"
        "docker compose down -v",
        s["code"]))

    st.append(Paragraph("Demo Credentials", s["h2"]))
    st.append(build_table(
        ["Field", "Value"],
        [
            ["URL", "http://localhost:9009/"],
            ["Email", "admin@example.com"],
            ["Password", "admin123"],
            ["Company", "DEMO"],
            ["Swagger Docs", "http://localhost:9009/api/v1/docs"],
            ["Health Check", "http://localhost:9009/health"],
        ],
        col_widths=[4 * cm, 13 * cm]
    ))
    st.append(PageBreak())

    # 2. Server Deployment
    st.append(Paragraph("2. Production Server Deployment", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Server Requirements", s["h2"]))
    st.append(build_table(
        ["Provider", "Instance", "Specs", "Monthly Cost"],
        [
            ["DigitalOcean", "Basic Droplet", "4 vCPU, 8GB RAM, 100GB SSD", "~$40 (1,400 EGP)"],
            ["Hetzner Cloud", "CPX41", "8 vCPU, 16GB RAM, 240GB SSD", "~$35 (1,225 EGP)"],
            ["AWS EC2", "t3.large", "2 vCPU, 8GB RAM, 100GB EBS", "~$60 (2,100 EGP)"],
            ["Vultr", "Cloud Compute", "4 vCPU, 8GB RAM, 200GB SSD", "~$48 (1,680 EGP)"],
            ["Local VPS (Egypt)", "Various", "4 vCPU, 8GB RAM, 100GB SSD", "1,500-3,000 EGP"],
        ],
        col_widths=[3 * cm, 3 * cm, 5.5 * cm, 4.5 * cm]
    ))

    st.append(Paragraph("Step-by-Step Deployment", s["h2"]))
    deploy_steps = [
        ("Step 1: Install Docker", "# Update system<br/>"
         "sudo apt update && sudo apt upgrade -y<br/><br/>"
         "# Install Docker<br/>"
         "curl -fsSL https://get.docker.com | sh<br/><br/>"
         "# Add user to docker group<br/>"
         "sudo usermod -aG docker $USER<br/>"
         "newgrp docker<br/><br/>"
         "# Verify<br/>"
         "docker --version  # Should show 24+"),
        ("Step 2: Copy Project", "# Clone or copy project<br/>"
         "scp -r ./ERP_System user@server:/opt/erp<br/>"
         "ssh user@server<br/>"
         "cd /opt/erp"),
        ("Step 3: Configure Environment", "# Copy template<br/>"
         "cp .env.example .env<br/><br/>"
         "# Generate secret key<br/>"
         "python3 -c \"import secrets; print(secrets.token_hex(32))\"<br/><br/>"
         "# Edit .env<br/>"
         "nano .env<br/><br/>"
         "# Required changes:<br/>"
         "# SECRET_KEY=<generated key><br/>"
         "# POSTGRES_PASSWORD=&lt;your-password&gt;<br/>"
         "# APP_ENV=production<br/>"
         "# DEBUG=false"),
        ("Step 4: Start Services", "# Build and start<br/>"
         "docker compose up --build -d<br/><br/>"
         "# Wait for health check<br/>"
         "curl http://localhost:9009/health<br/>"
         "# Should return: {\"status\": \"ok\", ...}"),
        ("Step 5: Create Admin User", "# Seed demo data<br/>"
         "docker compose exec -T web python -m scripts.seed<br/><br/>"
         "# Or create custom admin<br/>"
         "docker compose exec -T web python -m scripts.seed<br/>"
         "  --admin-email admin@yourcompany.com<br/>"
         "  --admin-password 'YourSecurePassword!'"),
        ("Step 6: Set Up Backups", "# Make backup script executable<br/>"
         "chmod +x scripts/backup_db.sh<br/><br/>"
         "# Add to crontab (daily at 2 AM)<br/>"
         "crontab -e<br/>"
         "0 2 * * * cd /opt/erp && ./scripts/backup_db.sh >> backups/backup.log 2>&1"),
    ]
    for title, code in deploy_steps:
        st.append(Paragraph(title, s["h3"]))
        st.append(Paragraph(code, s["code"]))
        st.append(Spacer(1, 0.2 * cm))
    st.append(PageBreak())

    # 3. Domain & SSL
    st.append(Paragraph("3. Domain & SSL Configuration", s["h1"]))
    st.append(hr())

    st.append(Paragraph("DNS Setup", s["h2"]))
    st.append(Paragraph(
        "Create a DNS A record pointing your domain to your server's public IP address:",
        s["body"]))
    st.append(Paragraph(
        "Type: A  |  Name: erp  |  Value: YOUR_SERVER_IP  |  TTL: 3600",
        s["code"]))
    st.append(Paragraph(
        "This creates erp.yourdomain.com pointing to your server. "
        "DNS propagation may take 5 minutes to 48 hours.",
        s["body"]))

    st.append(Paragraph("Option A: Caddy (Recommended)", s["h2"]))
    st.append(Paragraph(
        "Caddy automatically obtains and renews SSL certificates via Let's Encrypt. "
        "Zero configuration required for HTTPS.",
        s["body"]))
    st.append(Paragraph(
        "# Install Caddy<br/>"
        "sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https<br/>"
"curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' |<br/>"
         "  sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg<br/>"
         "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' |<br/>"
        "  sudo tee /etc/apt/sources.list.d/caddy-stable.list<br/>"
        "sudo apt update && sudo apt install caddy<br/><br/>"
        "# Configure<br/>"
        "sudo nano /etc/caddy/Caddyfile<br/><br/>"
        "# Content:<br/>"
        "erp.yourdomain.com {<br/>"
        "    reverse_proxy localhost:9009<br/>"
        "}<br/><br/>"
        "# Restart<br/>"
        "sudo systemctl restart caddy<br/>"
        "sudo systemctl enable caddy",
        s["code"]))

    st.append(Paragraph("Option B: Nginx + Certbot", s["h2"]))
    st.append(Paragraph(
        "# Install Nginx and Certbot<br/>"
        "sudo apt install nginx certbot python3-certbot-nginx<br/><br/>"
        "# Create Nginx config<br/>"
        "sudo nano /etc/nginx/sites-available/erp<br/><br/>"
        "# Content:<br/>"
        "server {<br/>"
        "    listen 80;<br/>"
        "    server_name erp.yourdomain.com;<br/><br/>"
        "    location /api/ {<br/>"
        "        proxy_pass http://127.0.0.1:9009;<br/>"
        "        proxy_set_header Host $host;<br/>"
        "        proxy_set_header X-Real-IP $remote_addr;<br/>"
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;<br/>"
        "        proxy_set_header X-Forwarded-Proto $scheme;<br/>"
        "    }<br/><br/>"
        "    location / {<br/>"
        "        proxy_pass http://127.0.0.1:9009;<br/>"
        "        proxy_set_header Host $host;<br/>"
        "    }<br/>"
        "}<br/><br/>"
        "# Enable and get SSL<br/>"
        "sudo ln -s /etc/nginx/sites-available/erp /etc/nginx/sites-enabled/<br/>"
        "sudo nginx -t && sudo systemctl reload nginx<br/>"
        "sudo certbot --nginx -d erp.yourdomain.com",
        s["code"]))
    st.append(PageBreak())

    # 4. Multi-Tenant Architecture
    st.append(Paragraph("4. Multi-Tenant Architecture", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "ERP Pro uses a Shared Database architecture — all companies reside in the same PostgreSQL "
        "database, isolated by company_id foreign keys on every business table. This is the most "
        "cost-effective and operationally simple model for SaaS deployments.",
        s["body"]))

    st.append(Paragraph("What Each Company Gets", s["h2"]))
    st.append(build_table(
        ["Resource", "Scope", "Isolation Method"],
        [
            ["Company Profile", "Per company", "Unique id, name, code, settings"],
            ["Branches", "Per company", "Branch records linked by company_id"],
            ["Users", "Shared identity", "user_roles links users to companies with roles"],
            ["Roles & Permissions", "Per company", "Roles and permissions scoped to company_id"],
            ["Items & Categories", "Per company", "All item tables have company_id FK"],
            ["Partners", "Per company", "partners.company_id FK"],
            ["Warehouses & Stock", "Per company", "warehouse_stock.company_id FK"],
            ["Invoices", "Per company", "sales_invoices.company_id FK"],
            ["Payments", "Per company", "payments.company_id FK"],
            ["Journal Entries", "Per company", "journal_entries.company_id FK"],
            ["Numbering Sequences", "Per company", "Numbering is sequential per company"],
            ["Module Settings", "Per company", "company_settings.enabled_modules"],
        ],
        col_widths=[4 * cm, 3 * cm, 10 * cm]
    ))

    st.append(Paragraph("Data Isolation Enforcement", s["h2"]))
    st.append(Paragraph(
        "Every API request that touches business data passes through the get_current_company_id() "
        "dependency. This reads the current_company_id from the user's auth session and returns "
        "it to the route handler. All subsequent queries filter by this company_id.",
        s["body"]))
    st.append(Paragraph(
        "If a user tries to access data from a company they don't have a role in, the system "
        "returns HTTP 403 Forbidden. If no company is selected (session not scoped), the system "
        "returns HTTP 409 Conflict.",
        s["body"]))

    st.append(Paragraph("Superuser Access", s["h2"]))
    st.append(Paragraph(
        "Users with is_superuser=True bypass all company-scoping and permission checks. They "
        "can access the Platform admin panel to manage all tenants, create companies, reset "
        "passwords, and view all data. Use sparingly and only for system administrators.",
        s["body"]))
    st.append(PageBreak())

    # 5. Adding New Companies
    st.append(Paragraph("5. Adding New Companies", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Method 1: SuperAdmin Panel (Recommended)", s["h2"]))
    steps = [
        "1. Login as superuser (admin@example.com / admin123)",
        "2. Navigate to SuperAdmin in the sidebar",
        "3. Click 'Create Company'",
        "4. Fill in: Company Name, Code, Base Currency (EGP), Activity Type",
        "5. Enable desired modules (Sales, Purchases, Inventory, etc.)",
        "6. System auto-creates: Company + Main Branch + Admin Role + Admin User",
        "7. Share the admin credentials with the company owner",
    ]
    for step in steps:
        st.append(Paragraph(step, s["bullet"]))

    st.append(Paragraph("Method 2: API Direct", s["h2"]))
    st.append(Paragraph(
        "POST /api/v1/platform/companies<br/>"
        "Authorization: Bearer &lt;superuser_token&gt;<br/>"
        "Content-Type: application/json<br/><br/>"
        "{<br/>"
        '  "name": "Acme Trading Co",<br/>'
        '  "code": "ACME",<br/>'
        '  "base_currency": "EGP",<br/>'
        '  "activity_type": "trading",<br/>'
        '  "admin_email": "admin@acme.com",<br/>'
        '  "admin_password": "SecureP@ss2026!",<br/>'
        '  "enabled_modules": ["sales", "purchases", "inventory", "accounting", "hr"]<br/>'
        "}",
        s["code"]))

    st.append(Paragraph("Method 3: Seed Script", s["h2"]))
    st.append(Paragraph(
"# Create a new company via seed script<br/>"
         "docker compose exec -T web python -m scripts.seed<br/>"
         "  --company-code ACME<br/>"
         "  --company-name 'Acme Trading'<br/>"
         "  --admin-email admin@acme.com<br/>"
        "  --admin-password 'SecureP@ss2026!'",
        s["code"]))

    st.append(Paragraph("What Gets Created Automatically", s["h2"]))
    st.append(build_table(
        ["Resource", "Details"],
        [
            ["Company", "Name, code, base_currency, activity_type, is_active=True"],
            ["Main Branch", "Code: MAIN, name: Main Branch"],
            ["Company Settings", "All modules enabled, cost_method: weighted_average"],
            ["Admin Role", "Name: Admin, all 63 permissions granted"],
            ["Admin User", "Email + password, is_superuser for platform access"],
            ["User Role", "Links admin user to company with Admin role"],
        ],
        col_widths=[4 * cm, 13 * cm]
    ))
    st.append(PageBreak())

    # 6. Security Hardening
    st.append(Paragraph("6. Security Hardening", s["h1"]))
    st.append(hr())

    hardening = [
        ("6.1 Change Default Secrets", "# Generate new SECRET_KEY<br/>"
         "python3 -c \"import secrets; print(secrets.token_hex(32))\"<br/><br/>"
         "# Update .env<br/>"
         "SECRET_KEY=&lt;new_key&gt;<br/><br/>"
         "# Restart<br/>"
         "docker compose restart web<br/><br/>"
         "WARNING: This invalidates all existing tokens. All users must re-login."),
        ("6.2 Change Database Password", "# Generate strong password<br/>"
         "python3 -c \"import secrets; print(secrets.token_urlsafe(20))\"<br/><br/>"
         "# Update .env<br/>"
         "POSTGRES_PASSWORD=&lt;new_password&gt;<br/><br/>"
         "# WARNING: This requires recreating the database<br/>"
         "# Backup first: ./scripts/backup_db.sh<br/>"
         "docker compose down -v<br/>"
         "docker compose up --build -d<br/>"
         "docker compose exec -T web python -m scripts.seed"),
        ("6.3 Firewall Rules", "# Enable UFW<br/>"
         "sudo ufw enable<br/><br/>"
         "# Allow only necessary ports<br/>"
         "sudo ufw allow 22/tcp    # SSH<br/>"
         "sudo ufw allow 80/tcp    # HTTP (redirects to HTTPS)<br/>"
         "sudo ufw allow 443/tcp   # HTTPS<br/><br/>"
         "# Block everything else<br/>"
         "sudo ufw default deny incoming<br/>"
         "sudo ufw default allow outgoing<br/><br/>"
         "# NEVER expose PostgreSQL (5432) or Redis (6379) to the internet"),
        ("6.4 Disable Debug Mode", "# In .env<br/>"
         "DEBUG=false<br/>"
         "APP_ENV=production<br/><br/>"
         "# This disables: Swagger docs in production,<br/>"
         "# verbose error messages, and development features"),
        ("6.5 Regular Updates", "# Update Docker images monthly<br/>"
         "docker compose pull<br/>"
         "docker compose up --build -d<br/><br/>"
         "# Update system packages<br/>"
         "sudo apt update && sudo apt upgrade -y"),
    ]
    for title, code in hardening:
        st.append(Paragraph(title, s["h2"]))
        st.append(Paragraph(code, s["code"]))
        st.append(Spacer(1, 0.3 * cm))
    st.append(PageBreak())

    # 7. Backup & Recovery
    st.append(Paragraph("7. Backup & Disaster Recovery", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Automated Backup", s["h2"]))
    st.append(Paragraph(
        "# Manual backup<br/>"
        "./scripts/backup_db.sh<br/><br/>"
        "# Automated daily backup (cron)<br/>"
        "crontab -e<br/>"
        "0 2 * * * cd /opt/erp && ./scripts/backup_db.sh >> backups/backup.log 2>&1<br/><br/>"
        "# Backup to custom directory<br/>"
        "./scripts/backup_db.sh /var/backups/erp",
        s["code"]))
    st.append(Paragraph(
        "Backups are stored as compressed SQL dumps in the backups/ directory. The script "
        "automatically keeps only the newest 14 files to manage disk usage.",
        s["body"]))

    st.append(Paragraph("Restore Procedure", s["h2"]))
    st.append(Paragraph(
        "# WARNING: This drops the existing database<br/>"
        "./scripts/restore_db.sh backups/erp_erp_20260810_120000.sql.gz<br/><br/>"
        "# Or manually<br/>"
        "gunzip -c backups/erp_erp_20260810_120000.sql.gz |<br/>"
        "  docker compose exec -T db psql -U erp -d erp",
        s["code"]))
    st.append(Paragraph(
        "<b>Always test your restore procedure before going live.</b> "
        "A backup that has never been tested is not a backup.",
        s["warning"]))

    st.append(Paragraph("Disaster Recovery Plan", s["h2"]))
    st.append(build_table(
        ["Metric", "Target", "Method"],
        [
            ["RPO (Recovery Point)", "24 hours", "Daily automated backups"],
            ["RTO (Recovery Time)", "1 hour", "Docker compose up from backup"],
            ["Backup Retention", "14 days", "Automatic pruning in backup script"],
            ["Off-site Backup", "Weekly", "Copy to S3 or alternative storage"],
            ["Restore Test", "Monthly", "Run restore on staging environment"],
        ],
        col_widths=[4 * cm, 4 * cm, 9 * cm]
    ))
    st.append(PageBreak())

    # 8. Monitoring
    st.append(Paragraph("8. Monitoring & Maintenance", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Health Check", s["h2"]))
    st.append(Paragraph(
        "curl http://localhost:9009/health<br/>"
        "# Returns: {\"status\": \"ok\", \"app\": \"ERP System\", \"environment\": \"production\",<br/>"
        "#          \"dependencies\": {\"database\": \"\", \"redis\": \"\"}}",
        s["code"]))

    st.append(Paragraph("Service Status", s["h2"]))
    st.append(Paragraph(
        "docker compose ps          # Show running containers<br/>"
        "docker compose logs web     # Backend logs<br/>"
        "docker compose logs frontend # Frontend/Nginx logs<br/>"
        "docker compose top          # Process info",
        s["code"]))

    st.append(Paragraph("Database Maintenance", s["h2"]))
    st.append(Paragraph(
        "# Connect to database<br/>"
        "docker compose exec db psql -U erp -d erp<br/><br/>"
        "# Check table sizes<br/>"
        "SELECT pg_size_pretty(pg_total_relation_size tablename)<br/>"
        "FROM pg_tables WHERE schemaname = 'public'<br/>"
        "ORDER BY pg_total_relation_size(tablename) DESC;<br/><br/>"
        "# Run VACUUM ANALYZE monthly<br/>"
        "docker compose exec db psql -U erp -d erp -c 'VACUUM ANALYZE;'",
        s["code"]))
    st.append(PageBreak())

    # 9. Troubleshooting
    st.append(Paragraph("9. Troubleshooting", s["h1"]))
    st.append(hr())

    st.append(build_table_left(
        ["Problem", "Cause", "Solution"],
        [
            ["Container won't start", "Port conflict", "Change ports in docker-compose.yml or stop conflicting service"],
            ["Database connection refused", "DB not ready", "Wait 30s or: docker compose restart web"],
            ["Migration errors", "Schema drift", "docker compose exec db psql -U erp -d erp -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' then re-seed"],
            ["Frontend 502 Bad Gateway", "Backend not running", "docker compose logs web to check errors"],
            ["Rate limit errors", "Redis issue", "Rate limiting degrades gracefully — check Redis: docker compose logs redis"],
            ["Token expired", "Session timeout", "User must re-login (default: 24h token lifetime)"],
            ["Permission denied (403)", "Missing role", "Assign appropriate role via SuperAdmin or Roles page"],
            ["Module not accessible (403)", "Module disabled", "Enable module in Company Settings or via API"],
            ["Disk space full", "Backup accumulation", "Backups auto-prune to 14; check: du -sh backups/"],
        ],
        col_widths=[4 * cm, 3 * cm, 10 * cm]
    ))

    doc.build(st, onFirstPage=page_number, onLaterPages=page_number)
    print(f"  ✓ {os.path.basename(path)}")


# ===========================================================================
# PDF 4 — User Manual
# ===========================================================================

def build_pdf4(path):
    doc = make_doc(path, "ERP Pro — User Manual")
    s = S()
    st = []

    # Cover
    st.append(Spacer(1, 6 * cm))
    st.append(Paragraph("User Manual", s["cover_title"]))
    st.append(Paragraph("Complete Guide to Every Module", s["cover_sub"]))
    st.append(Spacer(1, 1 * cm))
    st.append(Paragraph("Version 1.0  •  August 2026", s["cover_version"]))
    st.append(PageBreak())

    # TOC
    st.append(Paragraph("Table of Contents", s["h1"]))
    st.append(hr())
    for item in [
        "1. Login & Dashboard",
        "2. Company Settings & Roles",
        "3. Master Data (Items, Categories, Units)",
        "4. Partners (Customers & Suppliers)",
        "5. Currencies & Exchange Rates",
        "6. Sales",
        "7. Purchases",
        "8. Inventory & Warehouses",
        "9. Stock Takes",
        "10. Accounting",
        "11. Payments",
        "12. Human Resources",
        "13. Projects",
        "14. Manufacturing",
        "15. Point of Sale (POS)",
        "16. Reports",
        "17. Tips & Best Practices",
    ]:
        st.append(Paragraph(item, s["toc"]))
    st.append(PageBreak())

    # 1. Login
    st.append(Paragraph("1. Login & Dashboard", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Logging In", s["h2"]))
    st.append(Paragraph(
        "Open your web browser (Chrome, Firefox, Edge, or Safari) and navigate to the ERP URL "
        "provided by your administrator (e.g., https://erp.yourdomain.com or http://localhost:9009).",
        s["body"]))
    steps = [
        "1. Enter your email address in the Email field",
        "2. Enter your password in the Password field",
        "3. Click 'Sign In'",
        "4. If you belong to multiple companies, select the company you want to work in",
        "5. You are redirected to the Dashboard",
    ]
    for step in steps:
        st.append(Paragraph(step, s["bullet"]))

    st.append(Paragraph("Dashboard Overview", s["h2"]))
    st.append(Paragraph(
        "The Dashboard is your home screen. It shows four key performance indicators (KPIs) at the top:",
        s["body"]))
    kpis = [
        ("Total Revenue", "Sum of all confirmed sales invoices"),
        ("Net Profit", "Revenue minus cost of goods sold"),
        ("Inventory Value", "Total value of all stock across warehouses (quantity × average cost)"),
        ("Active Projects", "Number of projects with status 'active'"),
    ]
    for name, desc in kpis:
        st.append(Paragraph(f"•  <b>{name}</b>: {desc}", s["bullet"]))

    st.append(Paragraph(
        "Below the KPIs, you see three sections: Recent Sales (latest confirmed invoices), "
        "Recent Purchases (latest confirmed purchase invoices), and Inventory Snapshot (stock "
        "levels for tracked items).",
        s["body"]))

    st.append(Paragraph("Sidebar Navigation", s["h2"]))
    st.append(Paragraph(
        "The left sidebar contains navigation links organized into sections: Main (Dashboard, POS), "
        "Operations (Sales, Purchases, Inventory, Stock Takes, Manufacturing, Projects), Finance "
        "(Accounting, Payments, Reports, Currencies), HR (HR, Leave Requests), Master Data (Items, "
        "Partners), and Settings (Company Settings, Roles). The sidebar also includes a language "
        "toggle (EN/AR) and a theme toggle (Dark/Light) at the bottom.",
        s["body"]))
    st.append(PageBreak())

    # 2. Settings & Roles
    st.append(Paragraph("2. Company Settings & Roles", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Company Settings", s["h2"]))
    st.append(Paragraph(
        "Navigate to Settings > Company Settings. This page shows your current configuration "
        "and allows you to modify operational settings.",
        s["body"]))
    st.append(build_table(
        ["Setting", "Description", "Default"],
        [
            ["Enabled Modules", "Which modules are active for your company", "All 8 modules"],
            ["Cost Method", "Inventory costing method", "Weighted Average"],
            ["Max Users", "Maximum number of users allowed", "Plan-dependent"],
            ["Low Stock Threshold", "Default minimum stock level for alerts", "0 (disabled)"],
            ["Alert Emails", "Comma-separated emails for low-stock alerts", "None"],
            ["Block Negative Stock", "Prevent sales when stock reaches zero", "Enabled"],
        ],
        col_widths=[3.5 * cm, 9 * cm, 4.5 * cm]
    ))

    st.append(Paragraph("Roles & Permissions", s["h2"]))
    st.append(Paragraph(
        "Navigate to Settings > Roles. This page has two tabs: Roles and Users.",
        s["body"]))
    st.append(Paragraph("Creating a Custom Role:", s["h3"]))
    role_steps = [
        "1. Click the 'Roles' tab",
        "2. Click 'Create Role'",
        "3. Enter a role name (e.g., 'Sales Rep', 'Accountant', 'Warehouse Manager')",
        "4. After creation, click 'Edit Permissions' on the role card",
        "5. Check the permissions this role should have",
        "6. Save — the role is now available for assignment",
    ]
    for step in role_steps:
        st.append(Paragraph(step, s["bullet"]))

    st.append(Paragraph("Practical Example — Creating an Accountant Role:", s["h3"]))
    st.append(Paragraph(
        "1. Create role named 'Accountant'<br/>"
        "2. Grant these permissions:<br/>"
        "   ✓ accounting.view — View accounts and entries<br/>"
        "   ✓ accounting.manage — Create journal entries<br/>"
        "   ✓ accounting.reports — View financial reports<br/>"
        "   ✓ payments.view — View payment records<br/>"
        "   ✗ sales.view — Not needed for accounting<br/>"
        "   ✗ hr.view — Not needed for accounting<br/>"
        "   ✗ items.manage — Not needed for accounting",
        s["code"]))

    st.append(Paragraph("Adding a User:", s["h3"]))
    user_steps = [
        "1. Click the 'Users' tab",
        "2. Click 'Create User'",
        "3. Enter: Full Name, Email, Password (min 8 characters)",
        "4. Assign roles (comma-separated: 'Accountant, Sales Rep')",
        "5. The user can now login with the permissions from all assigned roles combined",
    ]
    for step in user_steps:
        st.append(Paragraph(step, s["bullet"]))
    st.append(PageBreak())

    # 3. Master Data
    st.append(Paragraph("3. Master Data", s["h1"]))
    st.append(hr())

    st.append(Paragraph("3.1 Item Categories", s["h2"]))
    st.append(Paragraph(
        "Navigate to Items & Products > Categories tab. Categories help organize your products "
        "into logical groups for reporting and filtering.",
        s["body"]))
    st.append(Paragraph(
        "To create a category:<br/>"
        "1. Click 'Add Category'<br/>"
        "2. Enter a name (e.g., 'Electronics', 'Office Supplies')<br/>"
        "3. Enter a code (e.g., 'ELEC', 'OFFICE') — must be unique per company<br/>"
        "4. Click 'Save Category'",
        s["body"]))

    st.append(Paragraph("3.2 Units of Measure", s["h2"]))
    st.append(Paragraph(
        "Navigate to Items & Products > Units tab. Units define how items are measured. "
        "Common units include: Piece (PCS), Kilogram (KG), Liter (LTR), Box (BOX), Meter (M).",
        s["body"]))
    st.append(Paragraph(
        "To create a unit:<br/>"
        "1. Click 'Add Unit'<br/>"
        "2. Enter name, code, and symbol (e.g., 'Piece', 'PCS', 'pc')<br/>"
        "3. Click 'Save Unit'",
        s["body"]))

    st.append(Paragraph("3.3 Unit Conversions", s["h2"]))
    st.append(Paragraph(
        "Navigate to Items & Products > Conversions tab. Unit conversions allow automatic "
        "conversion between different units. For example: 1 Box = 12 Pieces (factor = 12).",
        s["body"]))
    st.append(Paragraph(
        "To create a conversion:<br/>"
        "1. Click 'Add Conversion'<br/>"
        "2. Select 'From Unit' (e.g., Box)<br/>"
        "3. Select 'To Unit' (e.g., Piece)<br/>"
        "4. Enter the factor (e.g., 12 — meaning 1 Box = 12 Pieces)<br/>"
        "5. Click 'Save Conversion'",
        s["body"]))

    st.append(Paragraph("3.4 Items (Products & Services)", s["h2"]))
    st.append(Paragraph(
        "Navigate to Items & Products > Items tab. Items represent the products or services "
        "your company sells, buys, or uses.",
        s["body"]))
    st.append(build_table(
        ["Field", "Required", "Description", "Example"],
        [
            ["Name", "Yes", "Item name", "Wireless Mouse"],
            ["Code", "Auto", "Unique identifier (auto-generated if blank)", "WM-001"],
            ["Barcode", "No", "UPC/EAN barcode for POS scanning", "6901234567890"],
            ["Type", "Yes", "Stock (physical), Service, or Manufactured", "Stock"],
            ["Category", "No", "Item category for organization", "Electronics"],
            ["Base Unit", "No", "Primary unit of measure", "Piece"],
            ["Sale Price", "No", "Default selling price", "250.00"],
            ["Purchase Price", "No", "Default buying price", "150.00"],
            ["Min Stock", "No", "Low-stock alert threshold", "10"],
        ],
        col_widths=[2.5 * cm, 1.5 * cm, 8 * cm, 5 * cm]
    ))
    st.append(Paragraph(
        "<b>Item Types:</b><br/>"
        "• <b>Stock</b>: Physical products tracked in inventory. Stock levels change on sales/purchases.<br/>"
        "• <b>Service</b>: Non-physical items (consulting, delivery). No stock tracking.<br/>"
        "• <b>Manufactured</b>: Products made from other items using Bills of Materials.",
        s["body"]))
    st.append(PageBreak())

    # 4. Partners
    st.append(Paragraph("4. Partners (Customers & Suppliers)", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "Navigate to Partners. Partners represent the external entities your company does "
        "business with — customers who buy from you and suppliers who sell to you.",
        s["body"]))
    st.append(build_table(
        ["Field", "Required", "Description", "Example"],
        [
            ["Name", "Yes", "Partner name", "Mohamed Ahmed Trading"],
            ["Code", "Auto", "Unique identifier", "CUST-001"],
            ["Type", "Yes", "Customer, Supplier, or Both", "Customer"],
            ["Phone", "No", "Contact phone", "01012345678"],
            ["Email", "No", "Contact email", "info@ma-trading.com"],
            ["Address", "No", "Physical address", "Cairo, Egypt"],
            ["Tax Number", "No", "Tax registration number", "123-456-789"],
            ["Opening Balance", "No", "Starting balance owed/owing", "0.00"],
            ["Credit Limit", "No", "Maximum credit allowed (EGP)", "50,000"],
        ],
        col_widths=[2.5 * cm, 1.5 * cm, 8 * cm, 5 * cm]
    ))
    st.append(Paragraph(
        "<b>Partner Types:</b><br/>"
        "• <b>Customer</b>: A company or individual who buys from you. Appears in Sales invoices.<br/>"
        "• <b>Supplier</b>: A company or individual who sells to you. Appears in Purchase invoices.<br/>"
        "• <b>Both</b>: An entity that is both a customer and supplier.",
        s["body"]))
    st.append(PageBreak())

    # 5. Currencies
    st.append(Paragraph("5. Currencies & Exchange Rates", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "Navigate to Currencies. The base currency is set when the company is created (default: EGP). "
        "You can add additional currencies and configure exchange rates for multi-currency transactions.",
        s["body"]))
    st.append(Paragraph("Adding a Currency:", s["h3"]))
    st.append(Paragraph(
        "1. Click 'Currencies' tab<br/>"
        "2. Click 'Add Currency'<br/>"
        "3. Enter code (e.g., 'USD') and name (e.g., 'US Dollar')<br/>"
        "4. Click 'Save Currency'",
        s["body"]))
    st.append(Paragraph("Adding an Exchange Rate:", s["h3"]))
    st.append(Paragraph(
        "1. Click 'Exchange Rates' tab<br/>"
        "2. Click 'Add Rate'<br/>"
        "3. Select the currency (e.g., USD)<br/>"
        "4. Enter rate_to_base (e.g., 50.00 means 1 USD = 50 EGP)<br/>"
        "5. Set the valid_from date<br/>"
        "6. Click 'Save Rate'",
        s["body"]))
    st.append(Paragraph(
        "<b>Note:</b> When creating invoices in foreign currencies, the system uses the exchange rate "
        "to convert amounts to the base currency. The fx_gain_loss field on payments tracks "
        "any exchange rate differences.",
        s["note"]))
    st.append(PageBreak())

    # 6. Sales
    st.append(Paragraph("6. Sales", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "Navigate to Sales. This module manages the complete sales lifecycle from invoice "
        "creation through confirmation and stock deduction.",
        s["body"]))

    st.append(Paragraph("Creating a Sales Invoice:", s["h2"]))
    sales_steps = [
        "1. Click 'New Invoice'",
        "2. Select a customer from the dropdown (or leave blank for walk-in)",
        "3. The invoice number is auto-generated (e.g., SI-0001)",
        "4. Set the date (defaults to today)",
        "5. Optionally select a currency and exchange rate",
        "6. Add line items:",
        "   a. Select an item from the dropdown",
        "   b. Enter the quantity",
        "   c. Enter the unit price",
        "   d. The line total is calculated automatically (qty × price)",
        "7. Add more lines as needed",
        "8. Click 'Create Invoice' — status is now 'Draft'",
        "9. Review the invoice, then click 'Confirm' to finalize",
    ]
    for step in sales_steps:
        st.append(Paragraph(step, s["bullet"]))

    st.append(Paragraph("What Happens on Confirmation:", s["h2"]))
    st.append(Paragraph(
        "When you click Confirm, the system performs the following actions atomically:",
        s["body"]))
    effects = [
        "Invoice status changes from 'Draft' to 'Confirmed'",
        "For each line item: the quantity is deducted from warehouse_stock",
        "For each line item: the cost_price is set from the current average_cost",
        "For each line item: an inventory_movement record is created (type: sale_out)",
        "The total_amount and total_amount_base are calculated using the FX rate",
        "If block_negative_stock is enabled, the system checks stock before deduction",
    ]
    for e in effects:
        st.append(Paragraph(f"  →  {e}", s["sub_bullet"]))

    st.append(Paragraph("Practical Example:", s["h2"]))
    st.append(Paragraph(
        "Sell 3 Wireless Mice to customer 'Mohamed Ahmed Trading' at 250 EGP each:<br/><br/>"
        "1. Click 'New Invoice'<br/>"
        "2. Customer: Mohamed Ahmed Trading<br/>"
        "3. Line 1: Wireless Mouse × 3 @ 250.00 EGP = 750.00 EGP<br/>"
        "4. Total: 750.00 EGP<br/>"
        "5. Click 'Create Invoice' → Invoice #SI-0001 created (Draft)<br/>"
        "6. Click 'Confirm' → Stock reduced by 3, Invoice confirmed",
        s["body"]))
    st.append(PageBreak())

    # 7. Purchases
    st.append(Paragraph("7. Purchases", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "Navigate to Purchases. This module manages supplier invoices with automatic stock-in "
        "and weighted-average cost recalculation.",
        s["body"]))
    st.append(Paragraph("Creating a Purchase Invoice:", s["h2"]))
    st.append(Paragraph(
        "1. Click 'New Invoice'<br/>"
        "2. Select a supplier from the dropdown<br/>"
        "3. Add line items: select item, enter quantity and unit cost<br/>"
        "4. Click 'Create Invoice' (status: Draft)<br/>"
        "5. Click 'Confirm & Stock In' to finalize",
        s["body"]))
    st.append(Paragraph("What Happens on Confirmation:", s["h2"]))
    st.append(Paragraph(
        "Purchase confirmation triggers different logic than sales:<br/>"
        "• Stock is ADDED to the warehouse (not deducted)<br/>"
        "• Weighted-Average Cost (WAC) is recalculated:<br/>"
        "  new_avg = (old_qty × old_avg + new_qty × unit_cost) / (old_qty + new_qty)<br/>"
        "• This ensures the average cost reflects all purchases at their actual costs",
        s["body"]))

    st.append(Paragraph("Practical Example:", s["h2"]))
    st.append(Paragraph(
        "Buy 100 Wireless Mice from 'Nile Trading Co' at 150 EGP each:<br/><br/>"
        "1. Supplier: Nile Trading Co<br/>"
        "2. Line 1: Wireless Mouse × 100 @ 150.00 EGP = 15,000.00 EGP<br/>"
        "3. Total: 15,000.00 EGP<br/>"
        "4. Click 'Create Invoice' → Invoice #PI-0001 created (Draft)<br/>"
        "5. Click 'Confirm & Stock In' → Stock increased by 100<br/>"
        "6. If previous avg cost was 160 and old qty was 50:<br/>"
        "   new_avg = (50 × 160 + 100 × 150) / (50 + 100) = 153.33 EGP",
        s["body"]))
    st.append(PageBreak())

    # 8. Inventory
    st.append(Paragraph("8. Inventory & Warehouses", s["h1"]))
    st.append(hr())

    st.append(Paragraph("Stock Balance", s["h2"]))
    st.append(Paragraph(
        "Navigate to Inventory > Stock Balance tab. Shows current quantity, average cost, and "
        "total value for each item in each warehouse. This is your real-time inventory overview.",
        s["body"]))

    st.append(Paragraph("Warehouses", s["h2"]))
    st.append(Paragraph(
        "Navigate to Inventory > Warehouses tab. Create warehouses to organize stock locations. "
        "Examples: Main Warehouse, Branch Warehouse, Returns Warehouse, Damaged Goods.",
        s["body"]))
    st.append(Paragraph(
        "To create a warehouse:<br/>"
        "1. Click 'Add Warehouse'<br/>"
        "2. Enter name and code<br/>"
        "3. Click 'Save Warehouse'",
        s["body"]))

    st.append(Paragraph("Inventory Movements", s["h2"]))
    st.append(Paragraph(
        "Navigate to Inventory > Movements tab. This is a read-only log of all stock changes. "
        "Every sale, purchase, manufacturing, and stock take adjustment creates a movement record. "
        "Movement types include: purchase_in, sale_out, manufacturing_in, manufacturing_out, "
        "transfer, and adjustment.",
        s["body"]))
    st.append(PageBreak())

    # 9. Stock Takes
    st.append(Paragraph("9. Stock Takes (Physical Counting)", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "Navigate to Stock Takes. Stock takes reconcile your physical inventory count with "
        "the system's book quantities. This is essential for accuracy.",
        s["body"]))
    st.append(Paragraph("Creating a Stock Take:", s["h2"]))
    st.append(Paragraph(
        "1. Click '+ New Stock Take'<br/>"
        "2. Select the warehouse to count<br/>"
        "3. Optionally add a reference and note<br/>"
        "4. Click 'Create Stock Take'<br/>"
        "5. Add items to count:<br/>"
        "   - Select an item<br/>"
        "   - The book_qty (system quantity) is shown automatically<br/>"
        "   - Enter the counted_qty (what you actually counted)<br/>"
        "   - The diff_qty (difference) is calculated automatically<br/>"
        "6. Add all items you want to count<br/>"
        "7. Click 'Post' to apply the adjustments",
        s["body"]))
    st.append(Paragraph(
        "<b>What Post does:</b> For each line where counted ≠ book, the system creates an "
        "inventory_movement of type 'adjustment' and updates warehouse_stock to match the "
        "physical count.",
        s["body"]))
    st.append(PageBreak())

    # 10. Accounting
    st.append(Paragraph("10. Accounting", s["h1"]))
    st.append(hr())

    st.append(Paragraph(
        "Navigate to Accounting. The accounting module provides double-entry bookkeeping with "
        "a pre-seeded chart of accounts, journal entries, and three financial reports.",
        s["body"]))

    st.append(Paragraph("Chart of Accounts", s["h2"]))
    st.append(Paragraph(
        "The system comes with 13 pre-seeded accounts. You can add more. Account types include: "
        "Asset, Liability, Equity, Revenue, COGS (Cost of Goods Sold), Expense, Receivable, "
        "Payable, Inventory, Cash/Bank.",
        s["body"]))
    st.append(build_table(
        ["Code", "Name", "Type", "Purpose"],
        [
            ["1000", "Cash", "Cash/Bank", "Physical cash on hand"],
            ["1100", "Accounts Receivable", "Receivable", "Money owed by customers"],
            ["1200", "Inventory", "Inventory", "Value of stock on hand"],
            ["1500", "Fixed Assets", "Asset", "Long-term assets"],
            ["2000", "Accounts Payable", "Payable", "Money owed to suppliers"],
            ["2100", "Sales Tax Payable", "Liability", "Collected tax to remit"],
            ["2200", "Salaries Payable", "Liability", "Owed employee salaries"],
            ["3000", "Owner's Equity", "Equity", "Owner's investment"],
            ["4000", "Sales Revenue", "Revenue", "Income from sales"],
            ["5000", "COGS", "COGS", "Cost of items sold"],
            ["6000", "Operating Expenses", "Expense", "General business expenses"],
            ["6100", "FX Gain", "Revenue", "Foreign exchange gains"],
            ["6200", "FX Loss", "Expense", "Foreign exchange losses"],
        ],
        col_widths=[2 * cm, 4 * cm, 3 * cm, 8 * cm]
    ))

    st.append(Paragraph("Journal Entries", s["h2"]))
    st.append(Paragraph(
        "Navigate to Accounting > Journal Entries tab. Each entry has a date, reference, "
        "optional notes, and multiple lines (debits and credits). The system validates that "
        "total debits equal total credits before allowing you to post.",
        s["body"]))
    st.append(Paragraph("Practical Example — Recording Rent Payment:", s["h3"]))
    st.append(Paragraph(
        "1. Click '+ New Entry'<br/>"
        "2. Date: 2026-08-01<br/>"
        "3. Reference: RENT-AUG-2026<br/>"
        "4. Add Line 1: Account = Operating Expenses, Debit = 5,000, Credit = 0<br/>"
        "5. Add Line 2: Account = Cash, Debit = 0, Credit = 5,000<br/>"
        "6. Balance check: Debit (5,000) = Credit (5,000) ✓<br/>"
        "7. Click 'Post Entry'",
        s["body"]))

    st.append(Paragraph("Financial Reports", s["h2"]))
    st.append(Paragraph(
        "Navigate to Accounting and click the report tabs:<br/>"
        "• <b>Trial Balance</b>: Lists all accounts with their debit and credit totals. "
        "Total debits must equal total credits.<br/>"
        "• <b>Income Statement</b>: Revenue - COGS - Operating Expenses = Net Income. "
        "Shows profitability for a period.<br/>"
        "• <b>Balance Sheet</b>: Assets = Liabilities + Equity. Shows financial position "
        "at a point in time.",
        s["body"]))
    st.append(PageBreak())

    # 11. Payments
    st.append(Paragraph("11. Payments", s["h1"]))
    st.append(hr())
    st.append(Paragraph(
        "Navigate to Payments. Record payments received from customers or made to suppliers.",
        s["body"]))
    st.append(Paragraph("Recording a Payment:", s["h2"]))
    st.append(Paragraph(
        "1. Click '+ New Payment'<br/>"
        "2. Select the partner (customer or supplier)<br/>"
        "3. Enter the amount in EGP<br/>"
        "4. Select the payment method (Cash, Card, Bank Transfer, or Cheque)<br/>"
        "5. Set the payment date<br/>"
        "6. Optionally add notes<br/>"
        "7. Click 'Save Payment'",
        s["body"]))
    st.append(Paragraph(
        "<b>Example:</b> Customer 'Mohamed Ahmed' pays 5,000 EGP in cash:<br/>"
        "Partner: Mohamed Ahmed Trading | Amount: 5,000 | Method: Cash | Date: Today",
        s["body"]))
    st.append(PageBreak())

    # 12. HR
    st.append(Paragraph("12. Human Resources", s["h1"]))
    st.append(hr())

    st.append(Paragraph("12.1 Departments", s["h2"]))
    st.append(Paragraph(
        "Navigate to HR > Departments tab. Create departments to organize employees. "
        "Common departments: Sales, Warehouse, Finance, IT, HR, Operations.",
        s["body"]))

    st.append(Paragraph("12.2 Employees", s["h2"]))
    st.append(Paragraph(
        "Navigate to HR > Employees tab.<br/>"
        "To add an employee:<br/>"
        "1. Click '+ Add Employee'<br/>"
        "2. Fill in: Name, Employee Number (auto-generated), Position, Department, "
        "Basic Salary (EGP), Hire Date<br/>"
        "3. Click 'Save Employee'",
        s["body"]))
    st.append(Paragraph(
        "<b>Example:</b> Add 'Sara Mohamed' as Sales Representative:<br/>"
        "Name: Sara Mohamed | Position: Sales Representative | Department: Sales<br/>"
        "Basic Salary: 8,000 EGP | Hire Date: 2026-01-15",
        s["body"]))

    st.append(Paragraph("12.3 Attendance", s["h2"]))
    st.append(Paragraph(
        "Navigate to HR > Attendance tab. Record daily attendance for employees. "
        "Statuses: Present, Absent, Half Day, Leave. This data feeds into payroll calculation.",
        s["body"]))

    st.append(Paragraph("12.4 Payroll", s["h2"]))
    st.append(Paragraph(
        "Navigate to HR > Payroll tab.<br/>"
        "1. Enter the payroll period (e.g., 2026-08)<br/>"
        "2. Click 'Run Payroll'<br/>"
        "3. System calculates for each active employee: Basic Salary - Deductions = Net Salary<br/>"
        "4. Review the generated payroll lines<br/>"
        "5. PayrollRun status changes to 'Confirmed'",
        s["body"]))

    st.append(Paragraph("12.5 Leave Requests", s["h2"]))
    st.append(Paragraph(
        "Navigate to Leave Requests.<br/>"
        "To submit a request:<br/>"
        "1. Click '+ New Request'<br/>"
        "2. Select employee, leave type (Annual, Sick, Unpaid)<br/>"
        "3. Set start and end dates<br/>"
        "4. Enter reason<br/>"
        "5. Submit — status is 'Pending'<br/>"
        "6. Manager can Approve or Reject",
        s["body"]))
    st.append(PageBreak())

    # 13. Projects
    st.append(Paragraph("13. Projects", s["h1"]))
    st.append(hr())
    st.append(Paragraph(
        "Navigate to Projects. Track project profitability with cost allocation across "
        "materials, labor, and overhead.",
        s["body"]))
    st.append(Paragraph("Creating a Project:", s["h2"]))
    st.append(Paragraph(
        "1. Click '+ New Project'<br/>"
        "2. Enter: Code (e.g., PRJ-001), Name, Client (partner), Contract Value (EGP)<br/>"
        "3. Set start and end dates<br/>"
        "4. Click 'Create Project'<br/>"
        "5. Add cost lines throughout the project:<br/>"
        "   - Material costs: raw materials, supplies<br/>"
        "   - Labor costs: worker hours × hourly rate<br/>"
        "   - Overhead costs: permits, transport, utilities<br/>"
        "6. When complete: click 'Complete'<br/>"
        "7. System calculates: Margin = Contract Value - Total Cost",
        s["body"]))
    st.append(Paragraph(
        "<b>Example:</b> Office Renovation Project<br/>"
        "Contract: 200,000 EGP | Materials: 80,000 | Labor: 60,000 | Overhead: 10,000<br/>"
        "Total Cost: 150,000 EGP | Margin: 50,000 EGP (25%)",
        s["body"]))
    st.append(PageBreak())

    # 14. Manufacturing
    st.append(Paragraph("14. Manufacturing", s["h1"]))
    st.append(hr())

    st.append(Paragraph("14.1 Bills of Materials (BOM)", s["h2"]))
    st.append(Paragraph(
        "Navigate to Manufacturing > BOMs tab. A BOM defines how to make a product from "
        "raw materials.",
        s["body"]))
    st.append(Paragraph(
        "To create a BOM:<br/>"
        "1. Click '+ New BOM'<br/>"
        "2. Name: 'Wireless Mouse Kit'<br/>"
        "3. Output Item: Wireless Mouse<br/>"
        "4. Output Quantity: 1<br/>"
        "5. Add Components:<br/>"
        "   - Mouse Body × 1<br/>"
        "   - Circuit Board × 1<br/>"
        "   - USB Cable × 1<br/>"
        "6. Click 'Save BOM'",
        s["body"]))

    st.append(Paragraph("14.2 Work Orders", s["h2"]))
    st.append(Paragraph(
        "Navigate to Manufacturing > Work Orders tab.<br/>"
        "1. Click '+ New Work Order'<br/>"
        "2. Select BOM (optional) or product directly<br/>"
        "3. Select warehouse for material consumption and output<br/>"
        "4. Enter planned quantity<br/>"
        "5. Click 'Create Work Order'<br/>"
        "6. Add labor costs (description, hours, hourly rate)<br/>"
        "7. Add overhead costs (description, amount)<br/>"
        "8. Click 'Finish' — materials consumed from warehouse, finished goods added",
        s["body"]))
    st.append(PageBreak())

    # 15. POS
    st.append(Paragraph("15. Point of Sale (POS)", s["h1"]))
    st.append(hr())
    st.append(Paragraph(
        "Navigate to POS. The POS module provides a session-based point of sale for retail "
        "operations with cash management.",
        s["body"]))
    st.append(Paragraph("Session Workflow:", s["h2"]))
    st.append(Paragraph(
        "1. Click 'Open Session' → Enter opening cash amount (e.g., 1,000 EGP)<br/>"
        "2. Browse/search products in the left panel<br/>"
        "3. Click a product to add to cart<br/>"
        "4. Adjust quantities as needed<br/>"
        "5. Click 'Pay' to complete the order<br/>"
        "6. Repeat for more orders throughout the day<br/>"
        "7. When done: Enter closing cash amount → Click 'Close Session'<br/><br/>"
        "System calculates:<br/>"
        "• Expected Cash = Opening Cash + Total Sales<br/>"
        "• Variance = Closing Cash - Expected Cash<br/>"
        "• Positive variance = overage, Negative = shortage",
        s["body"]))
    st.append(PageBreak())

    # 16. Reports
    st.append(Paragraph("16. Reports", s["h1"]))
    st.append(hr())
    st.append(Paragraph(
        "Navigate to Reports. The system provides four built-in reports:",
        s["body"]))
    st.append(build_table(
        ["Report", "Module", "What It Shows"],
        [
            ["Sales Summary", "Accounting", "Total invoices, amounts by status, grand total"],
            ["Stock Value", "Inventory", "Total inventory value, per-warehouse breakdown"],
            ["Low Stock", "Inventory", "Items below minimum stock level (needs attention)"],
            ["Project Costs", "Projects", "Cost breakdown per project with margin calculation"],
            ["Trial Balance", "Accounting", "All account balances (debits vs credits)"],
            ["Income Statement", "Accounting", "Revenue - COGS - Expenses = Net Income"],
            ["Balance Sheet", "Accounting", "Assets = Liabilities + Equity"],
        ],
        col_widths=[3.5 * cm, 3 * cm, 10.5 * cm]
    ))
    st.append(PageBreak())

    # 17. Tips
    st.append(Paragraph("17. Tips & Best Practices", s["h1"]))
    st.append(hr())

    tips = [
        ("<b>Always confirm purchase invoices</b> — this updates stock levels and average costs. "
         "Unconfirmed purchases don't affect inventory."),
        ("<b>Set min_stock_level on items</b> — this enables automatic low-stock alerts via email. "
         "Configure alert emails in Company Settings."),
        ("<b>Use stock takes periodically</b> — reconcile physical vs book quantities monthly "
         "to catch discrepancies early."),
        ("<b>Create roles with minimal permissions</b> — follow the principle of least privilege. "
         "A cashier doesn't need accounting access."),
        ("<b>Back up your database regularly</b> — the automated backup script keeps 14 days. "
         "Test your restore procedure monthly."),
        ("<b>Use the Danger Zone sparingly</b> — clearing company data is irreversible. "
         "Always create a backup first."),
        ("<b>Enable only needed modules</b> — reduces UI complexity and prevents unauthorized "
         "access to unused features."),
        ("<b>Set up alert emails</b> — configure multiple recipients in Company Settings to "
         "stay informed about low stock levels."),
        ("<b>Use barcodes on items</b> — significantly speeds up POS operations and stock takes."),
        ("<b>Review Trial Balance monthly</b> — catch accounting errors early before they compound."),
        ("<b>Use weighted average costing</b> — it's the default and provides the most accurate "
         "cost tracking for most businesses."),
        ("<b>Document your chart of accounts</b> — add descriptions to accounts so new team "
         "members understand what each account is for."),
    ]
    for i, tip in enumerate(tips, 1):
        st.append(Paragraph(f"{i}. {tip}", s["bullet"]))

    doc.build(st, onFirstPage=page_number, onLaterPages=page_number)
    print(f"  ✓ {os.path.basename(path)}")


# ===========================================================================
# Main
# ===========================================================================

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(output_dir, exist_ok=True)

    which = sys.argv[1] if len(sys.argv) > 1 else "all"

    builders = {
        "1": ("01_ERP_System_Documentation.pdf", build_pdf1),
        "2": ("02_Feasibility_Study_Pricing.pdf", build_pdf2),
        "3": ("03_Deployment_Guide.pdf", build_pdf3),
        "4": ("04_User_Manual.pdf", build_pdf4),
    }

    print("Generating ERP Pro documentation PDFs (English)...")
    print()

    for key, (filename, builder) in builders.items():
        if which in ("all", key):
            path = os.path.join(output_dir, filename)
            try:
                builder(path)
            except Exception as exc:
                print(f"  ✗ Failed: {filename} — {exc}")
                import traceback
                traceback.print_exc()

    print()
    print("Done! PDFs saved in docs/")


if __name__ == "__main__":
    main()

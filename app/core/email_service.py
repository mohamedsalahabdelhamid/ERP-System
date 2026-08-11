"""Email notification service for ERP alerts.

Handles sending emails for:
  - Low stock alerts (when stock falls below the configured threshold)
  - Stock exhaustion warnings

Uses Python's built-in smtplib. SMTP credentials are configured via environment
variables (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD).
Email sending is best-effort: failures are logged but never raise to callers.
"""

import logging
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email(
    to_addresses: list[str],
    subject: str,
    html_body: str,
) -> None:
    """Send an HTML email in a background thread (fire-and-forget)."""
    if not settings.SMTP_ENABLED:
        logger.info("SMTP disabled – skipping email: %s", subject)
        return
    if not to_addresses:
        return

    def _worker() -> None:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
            msg["To"] = ", ".join(to_addresses)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls()
                if settings.SMTP_USER:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.sendmail(settings.SMTP_FROM, to_addresses, msg.as_string())
            logger.info("Email sent to %s: %s", to_addresses, subject)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send email '%s': %s", subject, exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


def send_low_stock_alert(
    company_name: str,
    recipients: list[str],
    low_items: list[dict],
) -> None:
    """Send a low-stock alert email to the configured recipients.

    Args:
        company_name: Name of the company (used in the email subject).
        recipients: List of email addresses to send the alert to.
        low_items: List of dicts with keys:
                   item_name, item_code, current_qty, threshold_qty, warehouse_name
    """
    if not recipients or not low_items:
        return

    rows_html = ""
    for item in low_items:
        current = float(item.get("current_qty", 0))
        threshold = float(item.get("threshold_qty", 0))
        is_zero = current <= 0
        qty_color = "#ef4444" if is_zero else "#f59e0b"
        status_label = "❌ نفد المخزون" if is_zero else "⚠️ منخفض"
        rows_html += f"""
        <tr>
          <td style="padding:10px 16px;border-bottom:1px solid #334155;">{item.get("item_code","")}</td>
          <td style="padding:10px 16px;border-bottom:1px solid #334155;">{item.get("item_name","")}</td>
          <td style="padding:10px 16px;border-bottom:1px solid #334155;">{item.get("warehouse_name","")}</td>
          <td style="padding:10px 16px;border-bottom:1px solid #334155;
              color:{qty_color};font-weight:700;">{current:.2f}</td>
          <td style="padding:10px 16px;border-bottom:1px solid #334155;">{threshold:.2f}</td>
          <td style="padding:10px 16px;border-bottom:1px solid #334155;
              color:{qty_color};font-weight:700;">{status_label}</td>
        </tr>"""

    html_body = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>تنبيه مخزون</title></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:Arial,sans-serif;color:#f1f5f9;">
  <div style="max-width:720px;margin:32px auto;background:#1e293b;border-radius:16px;
              overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
    <!-- Header -->
    <div style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:28px 32px;">
      <h1 style="margin:0;font-size:22px;color:#fff;">⚡ ERP System — تنبيه المخزون</h1>
      <p style="margin:6px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">{company_name}</p>
    </div>
    <!-- Body -->
    <div style="padding:28px 32px;">
      <p style="margin:0 0 20px;font-size:15px;color:#94a3b8;">
        يُرجى مراجعة الأصناف التالية. وصل مخزونها إلى أقل من الحد الأدنى المحدد أو نفد بالكامل:
      </p>
      <table style="width:100%;border-collapse:collapse;background:#0f172a;border-radius:12px;
                    overflow:hidden;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;">
            <th style="padding:12px 16px;text-align:right;color:#64748b;font-weight:600;">الكود</th>
            <th style="padding:12px 16px;text-align:right;color:#64748b;font-weight:600;">اسم الصنف</th>
            <th style="padding:12px 16px;text-align:right;color:#64748b;font-weight:600;">المخزن</th>
            <th style="padding:12px 16px;text-align:right;color:#64748b;font-weight:600;">الكمية الحالية</th>
            <th style="padding:12px 16px;text-align:right;color:#64748b;font-weight:600;">الحد الأدنى</th>
            <th style="padding:12px 16px;text-align:right;color:#64748b;font-weight:600;">الحالة</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
      <p style="margin:20px 0 0;font-size:12px;color:#475569;">
        هذه رسالة تلقائية من نظام ERP. يُرجى عدم الرد عليها مباشرةً.
      </p>
    </div>
  </div>
</body>
</html>"""

    subject = f"[{company_name}] ⚠️ تنبيه: {len(low_items)} صنف وصل للحد الأدنى في المخزون"
    _send_email(recipients, subject, html_body)

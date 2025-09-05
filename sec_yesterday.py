#!/usr/bin/env python3
"""
sec_yesterday.py
Pull yesterday’s 8-K, DEF 14A and 13D filings and e-mail a short summary.
Tested on Python 3.8+
Author:  you
"""

import datetime as dt
import os
import feedparser
import yagmail

# ------------------------------------------------------------------
# USER SETTINGS – change these four lines only
# ------------------------------------------------------------------
EMAIL_TO      = "wrpryor1000@gmail.com"
EMAIL_FROM    = "wrpryor1000@gmail.com"
GMAIL_USER    = "wrpryor1000@gmail.com"   # or any Gmail / G-Suite address
GMAIL_PASS    = "cotl urev xaek hoan"  # never your real password!
# ------------------------------------------------------------------

FORMS = ("8-K", "DEF 14A", "13D")  # 13D also catches 13D/A
FEED  = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type={form}&company=&dateb=&owner=include&count=100&search_text=&output=atom"

def _yesterday():
    """Return yyyy-mm-dd for yesterday in US/Eastern (SEC time)."""
    # SEC uses UTC-5 / UTC-4; we approximate with local server time
    return (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

def fetch_filings(form: str, date: str):
    """Return list of (cik, name, link, summary) for *date*."""
    url = FEED.format(form=form)
    parsed = feedparser.parse(url)
    hits = []
    for entry in parsed.entries:
        # RSS <updated> or <published> is yyyy-mm-dd
        if not entry.get("updated") or not entry.updated.startswith(date):
            continue
        cik   = entry.edgar_ciknumber
        name  = entry.edgar_companyname
        link  = entry.link
        summ  = entry.title.replace(" – ", ": ").strip()
        hits.append((cik, name, link, summ))
    return hits

def build_email(date: str):
    """Return (subject, plain_text_body)."""
    lines = [f"SEC filings for {date}", "=" * 40, ""]
    empty = True
    for form in FORMS:
        filings = fetch_filings(form, date)
        if filings:
            empty = False
            lines.append(f"{form} filings ({len(filings)})")
            for cik, name, link, summ in filings:
                lines.append(f"  • {name} ({cik})")
                lines.append(f"    {summ}")
                lines.append(f"    {link}")
            lines.append("")
    if empty:
        lines.append("No 8-K, DEF 14A or 13D filings yesterday.")
    return f"SEC summary {date}", "\n".join(lines)

def send_mail(subject, body):
    with yagmail.SMTP(GMAIL_USER, GMAIL_PASS) as yag:
        yag.send(to=EMAIL_TO, subject=subject, contents=body)

def main():
    date = _yesterday()
    subject, body = build_email(date)
    send_mail(subject, body)
    print("Mail sent!")

if __name__ == "__main__":
    main()

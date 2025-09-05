#!/usr/bin/env python3
"""
sec_yesterday.py
Pull yesterday’s 8-K, DEF14A, 13D and 13G filings and e-mail a short summary.
Works on local machine OR inside GitHub Actions Ubuntu runner.
"""
import datetime as dt
import os
import feedparser
import yagmail

# ------------------------------------------------------------------
# 1.  Read credentials from environment (GitHub Actions) or fall
#     back to the hard-coded values below (local runs).
# ------------------------------------------------------------------
EMAIL_TO   = os.getenv("EMAIL_TO",   "wrpryor1000@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "wrpryor1000@gmail.com")
GMAIL_USER = os.getenv("GMAIL_USER", "wrpryor1000@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASS", "YOUR_APP_PASSWORD_HERE")  # replace for local runs

# ------------------------------------------------------------------
# 2.  Forms we want (NO spaces – keeps URLs clean).
# ------------------------------------------------------------------
FORMS = ("8-K", "DEF14A", "13D", "13G")

# SEC RSS endpoint – {} gets replaced with form type
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type={}&company=&dateb=&owner=include&count=100&search_text=&output=atom"

def _yesterday_utc():
    """Return yyyy-mm-dd string for yesterday in UTC (close enough for SEC daily feed)."""
    return (dt.datetime.utcnow().date() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

def fetch_filings(form: str, date: str):
    """Return list of (cik, name, link, summary) for *date*."""
    url = FEED.format(form)
    parsed = feedparser.parse(url)
    hits = []
    for entry in parsed.entries:
        # RSS <updated> tag starts with date
        if not entry.get("updated") or not entry.updated.startswith(date):
            continue
        cik  = entry.edgar_ciknumber
        name = entry.edgar_companyname
        link = entry.link
        summ = entry.title.replace(" – ", ": ").strip()
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
        lines.append("No 8-K, DEF14A, 13D or 13G filings yesterday.")
    return f"SEC summary {date}", "\n".join(lines)

def send_mail(subject, body):
    with yagmail.SMTP(GMAIL_USER, GMAIL_PASS) as yag:
        yag.send(to=EMAIL_TO, subject=subject, contents=body)

def main():
    date = _yesterday_utc()
    subject, body = build_email(date)
    send_mail(subject, body)
    print("Mail sent!")

if __name__ == "__main__":
    main()

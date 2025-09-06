#!/usr/bin/env python3
"""
sec_yesterday.py
Pull yesterday’s 8-K, DEF 14A, 13D, 13G filings and e-mail a short summary.
Uses US/Eastern calendar date and URL-encodes form types so spaces
(DEF 14A) and hyphens (8-K) are handled correctly.
"""
import datetime as dt
import os
import feedparser
import yagmail
import pytz
from urllib.parse import quote_plus
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type={}&company=&dateb=&owner=include&count=100&search_text=&output=atom"

url = FEED.format(quote_plus(form))

# ----------  date logic (US/Eastern)  ----------
EASTERN = pytz.timezone("US/Eastern")

def target_date() -> str:
    """Return yyyy-mm-dd in US/Eastern; env var DATE overrides."""
    if (override := os.getenv("DATE")):
        return override
    return (dt.datetime.now(EASTERN).date() - dt.timedelta(days=1)).isoformat()

# ----------  credentials  ----------
EMAIL_TO   = os.getenv("EMAIL_TO",   "wrpryor1000@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "wrpryor1000@gmail.com")
GMAIL_USER = os.getenv("GMAIL_USER", "wrpryor1000@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASS", "").replace(" ", "")

# ----------  forms (exact spelling)  ----------
FORMS = ("8-K", "DEF 14A", "13D", "13G")   # note the space in DEF 14A
FEED  = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type={}"
         "&company=&dateb=&owner=include&count=100&search_text=&output=atom")

# ----------  fetch  ----------
def fetch_filings(form: str, date: str):
    url = FEED.format(quote_plus(form))          # encode space / hyphen
    parsed = feedparser.parse(url)
    hits = []
    for entry in parsed.entries:
        accept = getattr(entry, "edgar_acceptancedatetime", None)
        if not accept:                           # skip if missing
            continue
        accept_date = accept[:10]                # yyyy-mm-dd part
        if accept_date != date:
            continue
        cik  = entry.edgar_ciknumber
        name = entry.edgar_companyname
        link = entry.link
        summ = entry.title.replace(" – ", ": ").strip()
        hits.append((cik, name, link, summ))
    return hits

# ----------  build message  ----------
def build_email(date: str):
    lines = [f"SEC filings for {date}  (acceptance date, US/Eastern)", "=" * 55, ""]
    empty = True
    for form in FORMS:
        filings = fetch_filings(form, date)
        if filings:
            empty = False
            lines.append(f"{form} filings ({len(filings)})")
            for cik, name, link, summ in filings:
                lines.append(f"  • {name}  (CIK {cik})")
                lines.append(f"    {summ}")
                lines.append(f"    {link}")
            lines.append("")
    if empty:
        lines.append("No 8-K, DEF 14A, 13D or 13G filings found for that date.")
    return f"SEC summary {date}", "\n".join(lines)

# ----------  send  ----------
def send_mail(subject, body):
    with yagmail.SMTP(GMAIL_USER, GMAIL_PASS) as yag:
        yag.send(to=EMAIL_TO, subject=subject, contents=body)

# ----------  main  ----------
def main():
    date = target_date()
    print(f"Querying SEC for acceptance date: {date}")
    subject, body = build_email(date)
    send_mail(subject, body)
    print("Mail sent!")

if __name__ == "__main__":
    main()

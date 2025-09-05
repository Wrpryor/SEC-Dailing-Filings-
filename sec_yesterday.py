#!/usr/bin/env python3
"""
sec_yesterday.py
Pull yesterday’s 8-K, DEF14A, 13D, 13G filings and e-mail a short summary.
Uses US/Eastern time (SEC time-stamp zone) so UTC midnight does not give
a false "no filings" result.
"""
import datetime as dt
import os
import feedparser
import yagmail
import pytz

# ----------------------------------------------------------
# 1.  Pick the date we want (US/Eastern)
#      - default: yesterday  (SEC calendar)
#      - override:  env var  YYYY-MM-DD
# ----------------------------------------------------------
EASTERN = pytz.timezone("US/Eastern")

def target_date() -> str:
    """Return yyyy-mm-dd in US/Eastern; env var DATE overrides."""
    date_str = os.getenv("DATE")
    if date_str:
        return date_str
    # yesterday in Eastern time
    return (dt.datetime.now(EASTERN).date() - dt.timedelta(days=1)).isoformat()

# ----------------------------------------------------------
# 2.  Mail credentials – read from env (GitHub) or defaults
# ----------------------------------------------------------
EMAIL_TO   = os.getenv("EMAIL_TO",   "wrpryor1000@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "wrpryor1000@gmail.com")
GMAIL_USER = os.getenv("GMAIL_USER", "wrpryor1000@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_APP_PASS", "").replace(" ", "")   # strip spaces

# ----------------------------------------------------------
# 3.  Forms we scan  (NO spaces)
# ----------------------------------------------------------
FORMS = ("8-K", "DEF14A", "13D", "13G")
FEED  = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type={}&company=&dateb=&owner=include&count=100&search_text=&output=atom"

# ----------------------------------------------------------
# 4.  Fetch & build
# ----------------------------------------------------------
def fetch_filings(form: str, date: str):
    url = FEED.format(form)
    parsed = feedparser.parse(url)
    hits = []
    for entry in parsed.entries:
        if not entry.get("updated") or not entry.updated.startswith(date):
            continue
        cik  = entry.edgar_ciknumber
        name = entry.edgar_companyname
        link = entry.link
        summ = entry.title.replace(" – ", ": ").strip()
        hits.append((cik, name, link, summ))
    return hits

def build_email(date: str):
    lines = [f"SEC filings for {date}  (US/Eastern cutoff)", "=" * 50, ""]
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
        lines.append("No 8-K, DEF14A, 13D or 13G filings found for that date.")
    return f"SEC summary {date}", "\n".join(lines)

# ----------------------------------------------------------
# 5.  Send
# ----------------------------------------------------------
def send_mail(subject, body):
    with yagmail.SMTP(GMAIL_USER, GMAIL_PASS) as yag:
        yag.send(to=EMAIL_TO, subject=subject, contents=body)

def main():
    date = target_date()
    print(f"Querying SEC for date: {date}")
    subject, body = build_email(date)
    send_mail(subject, body)
    print("Mail sent!")

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, ssl
import os
from dotenv import load_dotenv

# Parameters:
# workstudy = "either" / "not_workstudy" / "workstudy"
# location = "on_campus" / "off_campus"
# hiringperiod = "fall_only" / "spring_only" / "summer_only" / "academic_year" / "entire_year"

def parse_page(workstudy="", location="", hiringperiod=""):

    url = "https://yes.umass.edu/portal/jobsearch?cmd=search"

    match workstudy:
        case "either":
            url += "&amp;search_workstudy=Either%20Work-Study%20or%20Not"
        case "not_workstudy":
            url += "&amp;search_workstudy=Not%20Work-Study"
        case "workstudy":
            url += "&amp;search_workstudy=Work-Study"
        case _:
            pass
    
    match location:
        case "on_campus":
            url += "&amp;search_location=On-Campus"
        case "off_campus":
            url += "&amp;search_location=Off-Campus"
        case _:
            pass

    match hiringperiod:
        case "fall_only":
            url += "&amp;search_hiringperiod=Fall%20semester%20only"
        case "spring_only":
            url += "&amp;search_hiringperiod=Spring%20semester%20only"
        case "summer_only":
            url += "&amp;search_hiringperiod=Summer%20only"
        case "academic_year":
            url += "&amp;search_hiringperiod=Academic%20Year%20(fall%20and%20spring%20semesters)"
        case "entire_year":
            url += "&amp;search_hiringperiod=Entire%20year"
        case _:
            pass

    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    table = soup.find("table", class_="table")
    rows = table.find_all("tr")

    jobs = []
    today = date.today()
    today = datetime(today.year, today.month, today.day)

    for row in rows:
        a = row.find("a")
        link = a.get("href") if a else ""
        cells = row.find_all("td")

        if len(cells) <= 2:
            continue

        posting_date = datetime.strptime(cells[1].text, "%m/%d/%Y")
        if (today - posting_date).days < 7:
            jobs.append({"title": cells[2].text, "link": link})
    
    return jobs

def create_body(jobs):
    body_html = "<html>\n<head></head>\n<body>\n"
    body_html += "<h3>This Week's UMass Job Listings</h3>\n<ul>\n"
    domain = "https://yes.umass.edu"

    for job in jobs:
        body_html += f'<li><a href="{domain + job["link"]}" target="_blank" rel="noopener noreferrer">{job["title"]}</a></li>\n'

    body_html += "</ul>\n</body>\n</html>"

    return body_html

def send_email(sender_email, app_password, receiver_email, body_html=None):
    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = receiver_email
    email_message['Subject'] = "Weekly UMass Job Listings"

    email_message.attach(MIMEText(body_html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, email_message.as_string())

def main():
    # change parameters based on your needs
    jobs = parse_page(workstudy="", location="", hiringperiod="")

    body_html = create_body(jobs)

    load_dotenv()
    app_password = os.getenv("APP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    
    send_email(sender_email, app_password, receiver_email, body_html)

if __name__ == "__main__":
    main()
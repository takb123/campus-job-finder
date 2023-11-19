from bs4 import BeautifulSoup
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, ssl
import os
import asyncio, aiohttp
from dotenv import load_dotenv

# Parameters:
# workstudy = "either" / "not_workstudy" / "workstudy"
# location = "on_campus" / "off_campus"
# hiringperiod = "fall_only" / "spring_only" / "summer_only" / "academic_year" / "entire_year"

async def collectUMassJobs(workstudy="", location="", hiringperiod=""):

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

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), "html.parser")

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
                if (today - posting_date).days < 2:
                    jobs.append({"title": cells[2].text, "link": link})
            
            return jobs

keywords = ["software", "web", "computer", "app", "data", "tech", "machine", "dev"]

def parseHandshakeData(results):
    jobs = []
    for result in results:
        postingDate = datetime.fromisoformat(result["created_at"]).date()
        if (datetime.today().date() - postingDate).days > 1:
            return jobs, True

        jobName = result["job_name"]
        employerName = result["job"]["employer_name"]
        jobID = result["job_id"]
        if any([key in jobName.lower() for key in keywords]):
            jobs.append({
                "jobName": jobName,
                "employerName": employerName,
                "jobID": jobID
            })
    return jobs, False

# Fill out the necessary cookies by visiting Handshake website,
# then Inspect Element, go to Storage tab, and view cookies.
# Idk if there are any better methods

async def collectHandshakeJobs(fulltime=False, parttime=False, internship=False):
    jobType = ""
    if fulltime:
        jobType = "&job.job_types[]=9" + jobType + "&employment_type_names[]=Full-Time"
    if parttime:
        jobType = "&job.job_types[]=9" + jobType + "&employment_type_names[]=Part-Time"
    if internship or not jobType:
        jobType = "&job.job_types[]=3" + jobType

    url = "https://app.joinhandshake.com/stu/postings?category=Posting&ajax=true&including_all_facets_in_searches=true&page={}&per_page=100&sort_direction=desc&sort_column=created_at" + jobType

    cookies = {
        "_trajectory_session": "",
        "hss-global": "",
        "iterableEmailCampaignId": "",
        "iterableEndUserId": "",
        "iterableMessageId": "",
        "iterableTemplateId": "",
        "production_40919653_incident-warning-banner-show": "",
        "production_activation_utm_campaign": "",
        "production_app_upsell_gate": "",
        "production_current_user": "",
        "production_js_on": "",
        "production_submitted_email_address": "",
        "production_utm_params": "",
    }

    session = aiohttp.ClientSession(headers={ "Accept": "application/json, text/javascript" }, cookies=cookies)

    jobs = []
    i = 1
    finished = False

    while not finished:
        async with session.get(url.format(i)) as response:
            data = await response.json()
            results = data["results"]
            newJobs, finished = parseHandshakeData(results)
            jobs.extend(newJobs)
            i += 1

    await session.close()
    return jobs

def createBody(umassJobs, handshakeJobs):
    bodyHtml = ["<html>\n<head></head>\n<body>"]
    bodyHtml.append("<h2>Today's Job Listings</h2>")

    umassDomain = "https://yes.umass.edu"
    bodyHtml.append("<h3>UMass Campus Jobs</h3><ul>")
    if not umassJobs:
        bodyHtml.append('<li>None</li>')
    for job in umassJobs:
        bodyHtml.append(f'<li><a href="{umassDomain + job["link"]}" target="_blank" rel="noopener noreferrer">{job["title"]}</a></li>')
    bodyHtml.append("</ul>")

    handshakeDomain = "https://app.joinhandshake.com/stu/jobs/"
    bodyHtml.append("<h3>Handshake Jobs</h3><ul>")
    if not handshakeJobs:
        bodyHtml.append('<li>None</li>')
    for job in handshakeJobs:
        bodyHtml.append(f'<li><a href="{handshakeDomain + str(job["jobID"])}" target="_blank" rel="noopener" noreferrer>{job["jobName"]}</a><br>{job["employerName"]}</li>')
    bodyHtml.append("</ul>")

    bodyHtml.append("</body>\n</html>")
    return "\n".join(bodyHtml)

def sendEmail(senderEmail, appPassword, receiverEmail, bodyHtml=None):
    emailMessage = MIMEMultipart()
    emailMessage['From'] = senderEmail
    emailMessage['To'] = receiverEmail
    emailMessage['Subject'] = "Daily Job Listings"

    emailMessage.attach(MIMEText(bodyHtml, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(senderEmail, appPassword)
        server.sendmail(senderEmail, receiverEmail, emailMessage.as_string())

async def main():
    umassJobs, handshakeJobs = await asyncio.gather(collectUMassJobs(workstudy="not_workstudy"), collectHandshakeJobs())

    bodyHtml = createBody(umassJobs, handshakeJobs)

    load_dotenv()
    appPassword = os.getenv("APP_PASSWORD")
    senderEmail = os.getenv("SENDER_EMAIL")
    receiverEmail = os.getenv("RECEIVER_EMAIL")
    
    sendEmail(senderEmail, appPassword, receiverEmail, bodyHtml)

if __name__ == "__main__":
    asyncio.run(main())
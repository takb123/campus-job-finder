# campus-job-finder
This program sends you weekly emails about the UMass campus job postings from the [Job Portal](https://yes.umass.edu/portal/jobsearch).

## Usage
1. Set up Virtual Environment

```console

# Create a Virtual Environment
$ python -m virtualenv venv_name

# Activate the Virtual Environment
$ source venv_name/bin/activate

# Install packages
$ pip install -r requirements.txt
```
2. [Create a Google app password](https://support.google.com/accounts/answer/185833?hl=en)
3. Set up `.env` file with the following variables

Note: the sender email must be the Google account that is associated with the app password

```
APP_PASSWORD=xxxxxxxxxxxxxxxx
SENDER_EMAIL=xxxxx@gmail.com
RECEIVER_EMAIL=xxxxx@example.com
```

4. Set up a cron job to run `jobsearch.py` every week
```console
# Open crontab config file
$ crontab -e
```
Add the following line to your config file
```
0 23 * * 0 /path/to/venv/bin/python /path/to/jobsearch.py
```
This script runs every Sunday (=0, fifth number) at 23:00 (first & second number); change the day and time as you like


# todo: must re-login into bbo in the browser everyday because of expiration. I can't quite understand the flow. Has to do with login, cookies, expiration.
# todo: File named tourney*-{BBO_USERNAME}.html) are rich with information such as player names. They should be explored, perhaps using pandas read_html()?

# requires BBO_USERNAME, BBO_PASSWORD, BBO_COOKIES be put into .env file. The value of BBO_COOKIES can be obtained from browser dev tools. Cut and paste the long line starting with cookie: myhands_token=

import requests
from bs4 import BeautifulSoup
import re
import pathlib
from datetime import datetime, timezone, date
from dateutil import relativedelta
from time import sleep, mktime
from random import uniform
import os
from dotenv import load_dotenv  # use pip install python-dotenv

"""
# Not sure what's going on with cookies and login. Sometimes this source file's request() fail returning an html asking for login. Maybe every 24 hours?
# What seems to anecdotally fix the issue is to execute the below powershell command. It's the canonical WebRequest, cut down from selecting 'copy as powershell' using dev tools in the chrome.
# Afterwards executing, this source file works again.
# The cookies dict below are copy and pasted values from the 'copy as powershell'.
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.Cookies.Add((New-Object System.Net.Cookie("myhands_token", "bsalita%7C65fd9de9d4d9124bb9043672799d14187e5e90fb", "/", "www.bridgebase.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("PHPSESSID", "8ld82a4hb2g409jnsif1538g95", "/", "www.bridgebase.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("SRV", "www1.dal13.sl", "/", ".bridgebase.com")))
Invoke-WebRequest -OutFile o.html -UseBasicParsing -Uri "https://www.bridgebase.com/myhands/hands.php?username=bsalita&start_time=1677801600&end_time=1680393600" `
-WebSession $session
 """

cookies = {
    # "/", "www.bridgebase.com"
    "myhands_token": "bsalita%7C65fd9de9d4d9124bb9043672799d14187e5e90fb",
    "PHPSESSID": "8ld82a4hb2g409jnsif1538g95",  # "/", "www.bridgebase.com",
    "SRV": "www1.dal13.sl",  # "/", ".bridgebase.com"
}


def BBO_Download_Lin_File(fetchlin, username):

    results = re.search(
        r"^fetchlin\.php\?id\=(\d*)\&when\_played\=(\d*)$", fetchlin)
    assert results is not None, results

    lin_id = results.group(1)
    print(f"{lin_id=}")

    lin_epoch = int(results.group(2))
    print(f"{lin_epoch=}")

    # todo: check if utc is correct timezone.
    dt = datetime.utcfromtimestamp(lin_epoch)
    dts = dt.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Date: {dts=}")

    linfile = dataPath.joinpath(f"{lin_id}-{lin_epoch}-{username}.lin")
    print(f"{linfile=}")
    if not linfile.exists() or linfile.stat().st_size < 100:
        lin_url = "https://www.bridgebase.com/myhands/" + fetchlin
        print(f"{lin_url=}")
        response = session.get(lin_url, cookies=cookies)
        assert response.status_code == 200, [lin_url, response.status_code]
        assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'
        # print(response.text)
        # encoding='utf8' was needed for 3338576362-1678052162-Susie Q46.lin
        with open(linfile, 'w', encoding='utf8') as f:
            f.write(response.text)
        # Sleep a random number of seconds (between 1 and 5)
        sleep(uniform(.5, 2))


def BBO_Download_Lin_Files_Batch(session, start_date, end_date):

    start_date_epoch = int(mktime(start_date.timetuple()))
    end_date_epoch = int(mktime(end_date.timetuple()))
    print(f"{start_date_epoch=} {end_date_epoch=}")
    url = f"https://www.bridgebase.com/myhands/hands.php?username={BBO_USERNAME}&start_time={start_date_epoch}&end_time={end_date_epoch}"

#    for c in session.cookies.get_dict():
#        print(f"\nsession-cookie: {c}:{session.cookies[c]}")
#        cookies[c] = session.cookies[c]

    response = session.get(url, cookies=cookies)
    #driver = webdriver.Chrome()
    #response = driver.get(url)
    # driver.get(url)

    # with open('hand-content.txt', 'w', encoding='utf8') as f: # using encoding='utf8' for content file
    #    f.write(driver.page_source)

    # Set the headers in the browser
    # for key, value in headers.items():
    #    driver.add_cookie({'name': key, 'value': value})

    # Set the cookies in the browser
    # for key, value in cookies.items():
    #    driver.add_cookie({'name': key, 'value': value})

    # Refresh the page to apply the cookies and headers
    # driver.refresh()

    # print(driver.page_source)

    assert response.status_code == 200, [url, response.status_code]

    # driver.execute_script(response.text)
    # print the response dictionary
    # print(f"{session}")  # .cookies) #.get_dict())

    for c in session.cookies.get_dict():
        print(f"\nsession-cookie: {c}:{session.cookies[c]}")

    # using encoding='utf8' for cookie file
    with open('hands-cookies.txt', 'w', encoding='utf8') as f:
        for c in session.cookies.get_dict():
            f.write(session.cookies[c])

    # using encoding='utf8' for content file
    with open('hand-content.txt', 'w', encoding='utf8') as f:
        f.write(response.text)

    assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'

    soup = BeautifulSoup(response.content, "html.parser")

    travellers = soup.find_all("a", href=re.compile(
        r"^\/myhands\/hands\.php\?traveller\="))

    for traveller in travellers:
        # e.g. href=/myhands/hands.php?traveller=56336-1676144521-31245064&amp;username={BBO_USERNAME}
        href = traveller["href"]
        print(f"\n{href=}")
        results = re.search(
            r"traveller\=(\d*\-\d*\-\d*).*username\=(.*)$", href)
        if results is None:
            print(f"Unable to parse href for filename, username. Skipping.")
            continue

        travellerfilename = results.group(1)
        print(f"{travellerfilename=}")

        travellerusername = results.group(2)
        print(f"{travellerusername=}")

        travellerfile = dataPath.joinpath(f"traveler-{travellerfilename}.html")
        print(f"{travellerfile=}")
        if True:  # not travellerfile.exists() or travellerfile.stat().st_size < 100:
            # e.g. href=https://www.bridgebase.com/myhands/hands.php?traveller=57082-1678160881-70196899&amp;username={BBO_USERNAME}
            traveller_url = "https://www.bridgebase.com" + href
            print(f"{traveller_url=}")
            # todo: use pd.read_html() instead?
            response = session.get(traveller_url, cookies=cookies)
            assert response.status_code == 200, [
                traveller_url, response.status_code]
            assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'
            # print(response.text)
            # using encoding='utf8' for html files
            with open(travellerfile, 'w', encoding='utf8') as f:
                f.write(response.text)
            # Sleep a random number of seconds (between 1 and 5)
            sleep(uniform(.5, 2))

            soup = BeautifulSoup(response.content, "html.parser")

            tourneySummary = soup.find("tr", {"class": "tourneySummary"})
            assert tourneySummary is not None
            # e.g. href=f"https://webutil.bridgebase.com/v2/tview.php?t=56336-1676144521&u={BBO_USERNAME}"
            tourneyName = tourneySummary.find("td", {"class": "tourneyName"})
            assert tourneyName is not None
            tourneyUrl = tourneyName.find('a')['href']
            print(f"{tourneyUrl=}")
            # todo: use pd.read_html() instead?
            # todo: explore tourneySummary file (tourney*-{BBO_USERNAME}.html). It's rich in information such as player names.
            response = session.get(tourneyUrl, cookies=cookies)
            assert response.status_code == 200, [
                tourneyUrl, response.status_code]
            assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'
            # print(response.text)
            results = re.search(r'\?t\=(.*)\&', tourneyUrl)
            assert results is not None, tourneyUrl
            tourneyFile = dataPath.joinpath(
                'tourney-'+results.group(1)+'-'+travellerusername+'.html')
            print(f"{tourneyFile=} {tourneyFile.exists()=}")
            if not tourneyFile.exists() or tourneyFile.stat().st_size < 100:
                # using encoding='utf8' for html files
                with open(tourneyFile, 'w', encoding='utf8') as f:
                    f.write(response.text)
            # Sleep a random number of seconds (between 1 and 5)
            sleep(uniform(.5, 2))

            highlight = soup.find("tr", {"class": "highlight"})
            assert highlight is not None
            fetchlin = highlight.find(
                'a', href=re.compile(r"^fetchlin"))['href']
            assert fetchlin is not None
            BBO_Download_Lin_File(fetchlin, BBO_USERNAME)

            tourneys = soup.find_all("tr", {"class": "tourney"})
            assert tourneys is not None

            for tourney in tourneys:

                # e.g. fetchlin.php?id=3342405148&when_played=1678160881
                movie = tourney.find("td", {"class": "movie"})
                assert movie is not None, tourney

                # e.g. BBO_USERNAME
                onclick = movie.find('a')['onclick']
                assert onclick is not None, movie
                # e.g. onclick="hv_popuplin('pn|Joro_56,~~M44673,~~M44671, ...
                # don't know why (.*) doesn't work so using (\w*)
                results = re.search(r'pn\|([\w|\s]*),', onclick)
                if results is None:
                    print('Missing pn (player name) in onclick -- skipping')
                    continue
                tourneyUsername = results.group(1)
                print(f"{tourneyUsername=}")

                fetchlin = movie.find(href=re.compile(r"^fetchlin"))['href']
                assert fetchlin is not None, movie
                print(f"\n{fetchlin=}")

                BBO_Download_Lin_File(fetchlin, tourneyUsername)


def BBO_Download_Lin_Files(session, start_date, end_date):
    if isinstance(start_date, str):
        # todo: check if utc is correct timezone.
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        assert isinstance(start_date, date), type(start_date)
        start_date_dt = start_date
    if isinstance(end_date, str):
        # todo: check if utc is correct timezone.
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        assert isinstance(end_date, date), type(end_date)
        end_date_dt = end_date
    while start_date_dt < end_date_dt:
        next_month_dt = start_date_dt + \
            relativedelta.relativedelta(months=1, day=1)
        end_month_dt = min(next_month_dt, end_date_dt)
        print(f"{start_date_dt=} {end_month_dt=}")
        assert start_date_dt < end_month_dt
        BBO_Download_Lin_Files_Batch(session, start_date_dt, end_month_dt)
        start_date_dt = next_month_dt


# initialize global variables
load_dotenv()

# Initialize BBO_USERNAME, BBO_PASSWORD, BBO_COOKIES. They come from environment variables or from .env file. Requires that you create .env file containing your private values.
BBO_USERNAME = os.getenv('BBO_USERNAME')
assert BBO_USERNAME is not None
BBO_PASSWORD = os.getenv('BBO_PASSWORD')
assert BBO_PASSWORD is not None

# todo: this cookie code has been disabled until the interaction between cookies, login and expiration is understood.
# cookie: myhands_token=BBO_USERNAME... # appears to be static
BBO_COOKIES = os.getenv('BBO_COOKIES')
assert BBO_COOKIES is not None
# cookies = BBO_COOKIES.replace('^','') # remove any escape characters such as '^' which is a windows escape character

# Initialize start and end dates of desired downloads. Must be in YYYY-MM-DD format.
start_date = "2023-01-01"  # user modifyable
# user modifyable # or "2023-03-31" # todo: check if utc is correct timezone.
end_date = datetime.now(timezone.utc).date()

# initialize directory path to where data is to be stored.
dataPath = pathlib.Path('e:/bridge/data/bbo/data')  # user modifyable
dataPath.mkdir(parents=True, exist_ok=True)

# perform login

# Specify the login page URL and login credentials
url = "https://www.bridgebase.com/myhands/myhands_login.php"

data = {
    "username": BBO_USERNAME,
    "password": BBO_PASSWORD,
    'keep': True,
}

# Create a session object
session = requests.Session()

# Send a POST request to the login page with the payload to log in
response = session.post(url, data=data)

print(f"{session.cookies=}")

print(f"{response=}")

for c in session.cookies.get_dict():
    print(f"login-cookie: {c}:{session.cookies[c]}")

with open('login-cookies.txt', 'w', encoding='utf8') as f:  # using encoding='utf8' for cookies file
    for c in session.cookies.get_dict():
        f.write(session.cookies[c])

# Check if the login was successful by examining the response object
if response.status_code == 200:
    print("Login successful!")
else:
    print("Login failed.")
    quit()

assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'

# perform file downloads

# Call the function with start and end dates
BBO_Download_Lin_Files(session, start_date, end_date)

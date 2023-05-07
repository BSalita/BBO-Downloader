
# todo: must re-login into bbo in the browser everyday because of expiration. I can't quite understand the flow to be able to reproduce here. Is it that session cookies have to be passed to requests?

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
from dotenv import load_dotenv # use pip install python-dotenv

# nb: response.text uses unicode whereas response.content uses bytes

def BBO_Download_Lin_Files_Batch(session, start_date, end_date):
    start_date_epoch = int(mktime(start_date.timetuple()))
    end_date_epoch = int(mktime(end_date.timetuple()))
    print(f"{start_date_epoch=} {end_date_epoch=}")
    url = f"https://www.bridgebase.com/myhands/hands.php?username={BBO_USERNAME}&start_time=1675569600&end_time=1678161600"

    response = session.get(url, cookies={'cookie': cookies})
    assert response.status_code == 200, [url, response.status_code]
    assert 'Please login' not in response.text, 'Cookie failure?'

    # print the response dictionary
    #print(f"{session}")  # .cookies) #.get_dict())

    for c in session.cookies.get_dict():
        print(f"\nsession-cookie: {c}:{session.cookies[c]}")

    with open('hands-cookies.txt', 'w', encoding='utf8') as f: # using encoding='utf8' for cookie file
        for c in session.cookies.get_dict():
            f.write(session.cookies[c])

    with open('hand-content.txt', 'w', encoding='utf8') as f: # using encoding='utf8' for content file
        f.write(response.text)

    soup = BeautifulSoup(response.content, "html.parser")

    travellers_divs = soup.find_all("td", {"class": "traveller"})
    #print(travellers_divs, len(travellers_divs), type(travellers_divs))
    travellers = soup.find_all("a", href=re.compile(r"^\/myhands\/hands\.php\?traveller\="))

    for traveller in travellers:
        # e.g. href=/myhands/hands.php?traveller=56336-1676144521-31245064&amp;username=BBO_USERNAME
        href = traveller["href"]
        print(f"\n{href=}")
        results = re.search(
            r"traveller\=(\d*\-\d*\-\d*).*username\=(.*)$", href)
        assert results is not None, results

        travellerfilename = results.group(1)
        print("{travellerfilename=}")

        travellerusername = results.group(2)
        print(f"{travellerusername=}")
 
        travellerfile = dataPath.joinpath(f"traveler-{travellerfilename}.html")
        print(f"{travellerfile=}")
        if not travellerfile.exists() or travellerfile.stat().st_size < 100:
            traveller_url = "https://www.bridgebase.com" + href # e.g. href=https://www.bridgebase.com/myhands/hands.php?traveller=57082-1678160881-70196899&amp;username=BBO_USERNAME
            # todo: use pd.read_html() instead?
            response = session.get(traveller_url, cookies={'cookie': cookies})
            assert response.status_code == 200, [traveller_url, response.status_code]
            assert 'Please login' not in response.text, 'Cookie failure?'
            #print(response.text)
            with open(travellerfile, 'w', encoding='utf8') as f: # using encoding='utf8' for html files
                f.write(response.text)
            # Sleep a random number of seconds (between 1 and 5)
            sleep(uniform(.5, 2))

            soup = BeautifulSoup(response.content, "html.parser")
            tourneySummary = soup.find("tr", {"class": "tourneySummary"})
            assert tourneySummary is not None
            # e.g. href="https://webutil.bridgebase.com/v2/tview.php?t=56336-1676144521&u=BBO_USERNAME" 
            tourneyHRef = tourneySummary.find("td", {"class": "tourneyName"}).find('a')
            assert tourneyHRef is not None
            tourneyUrl = tourneyHRef['href']
            # todo: use pd.read_html() instead?
            response = session.get(tourneyUrl, cookies={'cookie': cookies})
            assert response.status_code == 200, [tourneyUrl, response.status_code]
            assert 'Please login' not in response.text, 'Cookie failure?'
            #print(response.text)
            results = re.search(r'\?t\=(.*)\&',tourneyUrl)
            assert results is not None, tourneyUrl
            tourneyFile = dataPath.joinpath('tourney-'+results.group(1)+'-'+travellerusername+'.html')
            if not travellerfile.exists() or travellerfile.stat().st_size < 100:
                with open(tourneyFile, 'w', encoding='utf8') as f: # using encoding='utf8' for html files
                    f.write(response.text)
            # Sleep a random number of seconds (between 1 and 5)
            sleep(uniform(.5, 2))

            highlight = soup.find_all("tr", {"class": "highlight"})
            assert highlight is not None

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
                results = re.search(r'pn\|([\w|\s]*),',onclick) # don't know why (.*) doesn't work so using (\w*)
                if results is None:
                    print('Missing pn (player name) in onclick -- skipping')
                    continue
                tourneyUsername = results.group(1)
                print(f"{tourneyUsername=}")

                fetchlin = movie.find(href=re.compile(r"^fetchlin"))['href']
                assert fetchlin is not None, movie

                print(f"\n{fetchlin=}")
                results = re.search(
                    r"^fetchlin\.php\?id\=(\d*)\&when\_played\=(\d*)$", fetchlin)
                assert results is not None, results

                lin_id = results.group(1)
                print(f"{lin_id=}")

                lin_epoch = int(results.group(2))
                print(f"{lin_epoch=}")
                dt = datetime.utcfromtimestamp(lin_epoch) # todo: check if utc is correct timezone.
                dts = dt.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Date: {dts=}")
        
                linfile = dataPath.joinpath(f"{lin_id}-{lin_epoch}-{tourneyUsername}.lin")
                print(f"{linfile=}")
                if not linfile.exists() or linfile.stat().st_size < 100:
                    lin_url = "https://www.bridgebase.com/myhands/" + fetchlin
                    response = session.get(lin_url, cookies={'cookie': cookies})
                    assert response.status_code == 200, [lin_url, response.status_code]
                    assert 'Please login' not in response.text, 'Cookie failure?'
                    #print(response.text)
                    with open(linfile, 'w') as f: # todo: check if encoding='utf8' is needed for lin files
                        f.write(response.text)
                    # Sleep a random number of seconds (between 1 and 5)
                    sleep(uniform(.5, 2))


def BBO_Download_Lin_Files(session, start_date, end_date):
    if isinstance(start_date,str):
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date() # todo: check if utc is correct timezone.
    else:
        assert isinstance(start_date,date), type(start_date)
        start_date_dt = start_date
    if isinstance(end_date,str):
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date() # todo: check if utc is correct timezone.
    else:
        assert isinstance(end_date,date), type(end_date)
        end_date_dt = end_date
    while start_date_dt < end_date_dt:
        next_month_dt = start_date_dt + relativedelta.relativedelta(months=1, day=1)
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
BBO_COOKIES = os.getenv('BBO_COOKIES') # cookie: myhands_token=BBO_USERNAME... # appears to be static
assert BBO_COOKIES is not None
cookies = BBO_COOKIES.replace('^','') # remove escapes '^' is windows character escape

# Initialize start and end dates of desired downloads. Must be in YYYY-MM-DD format.
start_date = "2023-01-01" # user modifyable
end_date = datetime.now(timezone.utc).date() # user modifyable # or "2023-03-31" # todo: check if utc is correct timezone.

# initialize directory path to where data is to be stored.
dataPath = pathlib.Path('e:/bridge/data/bbo/data') # user modifyable
dataPath.mkdir(exist_ok=True)

# perform login

# Specify the login page URL and login credentials
url = "https://www.bridgebase.com/myhands/myhands_login.php"

data = {
    "username": BBO_USERNAME,
    "password": BBO_PASSWORD
}

# Create a session object
session = requests.Session()

# Send a POST request to the login page with the payload to log in
response = session.post(url, data=data)

print(f"{session.cookies=}")

print(f"{response=}")

for c in session.cookies.get_dict():
    print(f"login-cookie: {c}:{session.cookies[c]}")

with open('login-cookies.txt', 'w', encoding='utf8') as f: # using encoding='utf8' for cookies file
    for c in session.cookies.get_dict():
        f.write(session.cookies[c])

# Check if the login was successful by examining the response object
if response.status_code == 200:
    print("Login successful!")
else:
    print("Login failed.")
    quit()

assert 'Please login' not in response.text, 'Cookie failure?'

# perform file downloads

# Call the function with start and end dates
BBO_Download_Lin_Files(session, start_date, end_date)

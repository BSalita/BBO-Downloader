# downloads BBO .lin files by username and date range.

# next steps:
# bbo_parse_lin_files.ipynb creates bbo_bidding_sequences_table.py which is a table of all known BBO bids.
# acbl_club_results_hand_records_bidding_BBO.ipynb augments acbl club hand records with BBO bidding sequences.

# previous steps:
# none


# todo: must re-login into bbo in the browser everyday because of expiration. I can't quite understand the flow to avoid that. Has to do with interaction between login, cookies, expiration.
# todo: File named tourney*-{BBO_USERNAME}.html) are rich with information such as player names (oh wait, I don't see how that's done). They should be explored, perhaps using pandas read_html()?
# todo: use try statement to catch and retry connection errors

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
# Not sure what's going on with cookies and login. Sometimes this source file's request() fails to return the expected html instead returning html asking for login. Probably once every 24 hours.
# What seems to anecdotally fix the issue is to login to your BBO account then execute the below powershell command. If it works, you're good to restart this program.
# The below command is a canonical BBO WebRequest, cut down from selecting 'copy as powershell' using dev tools in the chrome.
# The cookies dict below are copy and pasted values from the 'copy as powershell'.
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.Cookies.Add((New-Object System.Net.Cookie("myhands_token", "bsalita%7C65fd9de9d4d9124bb9043672799d14187e5e90fb", "/", "www.bridgebase.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("PHPSESSID", "mbtmquei21fpieofv1irajvfrf", "/", "www.bridgebase.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("SRV", "www1.dal10.sl", "/", ".bridgebase.com")))
Invoke-WebRequest -OutFile o.html -UseBasicParsing -Uri "https://www.bridgebase.com/myhands/hands.php?username=bsalita&start_time=1677801600&end_time=1680393600" `
-WebSession $session
 """

cookies = {
    # "/", "www.bridgebase.com"
    "myhands_token": "bsalita%7C65fd9de9d4d9124bb9043672799d14187e5e90fb",
    "PHPSESSID": "mbtmquei21fpieofv1irajvfrf",  # "/", "www.bridgebase.com", # must be refreshed from time-to-time
    "SRV": "www1.dal10.sl",  # "/", ".bridgebase.com" # must be refreshed from time-to-time
}


def BBO_Download_Lin_File(session, fetchlin, username):

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
    if linfile.exists() and linfile.stat().st_size > 100:
        print(f"{linfile=} exists. Skipping.")
    else:
        lin_url = "https://www.bridgebase.com/myhands/" + fetchlin
        print(f"{lin_url=}")
        response = session.get(lin_url, cookies=cookies) # todo: use try statement to catch and retry connection errors
        assert response.status_code == 200, [lin_url, response.status_code]
        assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'
        # print(response.text)
        # encoding='utf8' was needed for 3338576362-1678052162-Susie Q46.lin
        with open(linfile, 'w', encoding='utf8') as f:
            f.write(response.text)
        # Sleep a random number of seconds (between 1 and 5)
        sleep(uniform(.5, 2))


def BBO_Download_Lin_Files_Batch(session, start_date, end_date, username):

    start_date_epoch = int(mktime(start_date.timetuple()))
    end_date_epoch = int(mktime(end_date.timetuple()))
    print(f"{start_date_epoch=} {end_date_epoch=}")
    url = f"https://www.bridgebase.com/myhands/hands.php?username={username}&start_time={start_date_epoch}&end_time={end_date_epoch}"

#    for c in session.cookies.get_dict():
#        print(f"\nsession-cookie: {c}:{session.cookies[c]}")
#        cookies[c] = session.cookies[c]

    response = session.get(url, cookies=cookies) # todo: use try statement to catch and retry connection errors
    #driver = webdriver.Chrome()
    #response = driver.get(url) # todo: use try statement to catch and retry connection errors
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
    assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'
    assert 'Javascript support is needed' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'

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

    # file contains many and varied tournaments each having a tourneySummary followed by a list of travellers (siblings, not children).
    # it's easier to just grab all the traveller links to process. Each traveller file has the same info as tourneySummary.
    # for now, reject non-Robot tourneys. Theory is we don't want partnership bidding data, only robot bidding.
    for traveller in travellers:
        # e.g. href=/myhands/hands.php?traveller=56336-1676144521-31245064&amp;username=username
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
        if travellerfile.exists() and travellerfile.stat().st_size > 100:
            print(f"{travellerfile=} exists. Skipping.")
        else:
            # e.g. href=https://www.bridgebase.com/myhands/hands.php?traveller=57082-1678160881-70196899&amp;username=username
            traveller_url = "https://www.bridgebase.com" + href
            print(f"{traveller_url=}")
            # todo: use pd.read_html() instead?
            response = session.get(traveller_url, cookies=cookies) # todo: use try statement to catch and retry connection errors
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
            # e.g. href=f"https://webutil.bridgebase.com/v2/tview.php?t=56336-1676144521&u={username}"
            tourneyName = tourneySummary.find("td", {"class": "tourneyName"})
            assert tourneyName is not None
            if 'Robot' not in tourneyName.text:
                print(f"Skipping non-Robot tourney: {tourneyName.text}")
                continue
            # todo: rereads same file for every traveler file of same tourney. how to make it skip? create dict where?
            tourneyUrl = tourneyName.find('a')['href']
            print(f"{tourneyUrl=}")
            # todo: use pd.read_html() instead?
            # todo: explore tourneySummary file (tourney*-{username}.html). It's rich in information such as some player names although I don't see the mechanism for retrieving them.
            response = session.get(tourneyUrl, cookies=cookies) # todo: use try statement to catch and retry connection errors
            assert response.status_code == 200, [
                tourneyUrl, response.status_code]
            assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'
            # print(response.text)
            results = re.search(r'\?t\=(.*)\&', tourneyUrl)
            assert results is not None, tourneyUrl
            tourneyFile = dataPath.joinpath(
                'tourney-'+results.group(1)+'-'+travellerusername+'.html')
            print(f"{tourneyFile=} {tourneyFile.exists()=}")
            if tourneyFile.exists() and tourneyFile.stat().st_size > 100:
                print(f"{tourneyFile=} exists. Skipping write file.")
            else:
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
            BBO_Download_Lin_File(session, fetchlin, username)

            tourneys = soup.find_all("tr", {"class": "tourney"})
            assert tourneys is not None

            for tourney in tourneys:

                # e.g. fetchlin.php?id=3342405148&when_played=1678160881
                movie = tourney.find("td", {"class": "movie"})
                assert movie is not None, tourney

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

                BBO_Download_Lin_File(session, fetchlin, tourneyUsername)


def BBO_Download_Lin_Files(session, start_date, end_date, username):
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
        BBO_Download_Lin_Files_Batch(
            session, start_date_dt, end_month_dt, username)
        start_date_dt = next_month_dt


def BBO_login(session, username, password):

    # perform login

    # Specify the login page URL and login credentials
    url = "https://www.bridgebase.com/myhands/myhands_login.php"

    data = {
        "username": username,
        "password": password,
        'keep': True,
    }

    # Send a POST request to the login page with the payload to log in
    response = session.post(url, data=data) # todo: use try statement to catch and retry connection errors

    print(f"{session.cookies=}")

    print(f"{response=}")

    for c in session.cookies.get_dict():
        print(f"login-cookie: {c}:{session.cookies[c]}")

    # using encoding='utf8' for cookies file
    with open('login-cookies.txt', 'w', encoding='utf8') as f:
        for c in session.cookies.get_dict():
            f.write(session.cookies[c])

    # Check if the login was successful by examining the response object
    if response.status_code == 200:
        print("Login successful!")
    else:
        print("Login failed.")
        quit()

    assert 'Please login' not in response.text, 'Cookie failure? Try (re)logging into BBO using your browser.'


if __name__ == '__main__':

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

    # Create a session object
    session = requests.Session()

    BBO_login(session, BBO_USERNAME, BBO_PASSWORD)

    # provide usernames of players who you wish to have their lin files downloaded. Any BBO player can be requested.
    # files will now be downloaded. if the files are already downloaded, processing will be bypassed until non-downloaded files are encounted. This makes restarts very quick.
    usernames = ['Leo LaSota',
    'bsalita',
    'run4it',
    'hahahapc',
    'mimihand',
    'patsy15',
    'Teacher916',
    'ps1352',
    'wannagolf5',
    'bkjswan',
    'GDBraiser',
    'Vandy7',
    'frj22',
    'RROOZZ1513',
    'ljshear',
    'rosewhite',
    'beatmama',
    'spareo',
    'HeleneG11',
    'adahnick',
    'keisler',
    'ioaia',
    'ShuShu2',
    'sil4',
    'bakh123',
    'dharam10',
    'laughlin',
    'verajohn',
    'MarciaKnow',
    'nanag05420',
    'Slqppy1',
    'binsk',
    'Calplayer9',
    'annalisae',
    'hagemimi',
    'Callo2',
    'wallaceng',
    'campbeconn',
    'fritz49',
    'Sweetpea66',
    'di28374',
    'fergie0809',
    'maryw76',
    'TahoeView',
    'riverwalk3',
    'leplbr4321',
    'ginfuller',
    'lorna216',
    'Hobo Jo',
    'jmino',
    'srenee',
    'crdsnrkt55',
    'dd5times',
    'Bcmom92',
    'bubbasween',
    'BernPorter',
    'amymack',
    'gpappalard',
    'fusion13',
    'vandood',
    'dgf4578282',
    'BIGBIRD48',
    'hichan',
    'badnews',
    'kathleen02',
    'lms2',
    'shaglady76',
    'margiebroo',
    'shark 2020',
    'mules422',
    'Smittycity',
    'kimpton',
    'jhlowy',
    'bellgol',
    'GT0903',
    'Twin454s',
    'Elle777',
    'llooiiee',
    'Hawkmoon1',
    'donalde',
    'kahus',
    'diannee',
    'PuppySr',
    'radcat',
    'Pefuller33',
    'cbiaspen',
    'rlb1953',
    'NashP1',
    'majov',
    'crdninja',
    'janewriter',
    'levrose',
    'BetteC8989',
    'kjbourne',
    'marincarol',
    'FrannieK',
    'outrage',
    'soleil601',
    'volvoo',
    'lengold']
    for username in usernames: # download lin files of some frequent players
        # perform file downloads for specified date range
        BBO_Download_Lin_Files(session, start_date, end_date, username)

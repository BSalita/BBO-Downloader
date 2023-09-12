# downloads BBO .lin files by username and date range.

# next steps:
# bbo_parse_lin_files.ipynb creates bbo_bidding_sequences_table.py which is a table of all known BBO bids.
# acbl_club_results_hand_records_bidding_BBO.ipynb augments acbl club hand records with BBO bidding sequences.

# previous steps:
# none


# todo: must re-login into bbo in the browser everyday(?) because of expiration. I can't quite understand the flow to avoid that.
# todo: File named tourney*-{BBO_USERNAME}.html) are rich with information such as player names (oh wait, I don't see how that's done). They should be explored, perhaps using pandas read_html()?
# todo: use try statement to catch and retry connection errors

# requires BBO_USERNAME, BBO_PASSWORD be put into .env file.

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

    linpath = dataPath.joinpath(username)
    if not linpath.exists():
        print(f"mkdir: {linpath}")
        linpath.mkdir()
    linfile = linpath.joinpath(f"{lin_id}-{lin_epoch}-{username}.lin")
    print(f"{linfile=}")
    if linfile.exists() and linfile.stat().st_size > 100:
        print(f"{linfile=} exists. Skipping.")
    else:
        lin_url = "https://www.bridgebase.com/myhands/" + fetchlin
        print(f"{lin_url=}")
        # todo: use try statement to catch and retry connection errors
        response = session.get(lin_url)
        assert response.status_code == 200, [lin_url, response.status_code]
        assert 'Please login' not in response.text, 'BBO_Download_Lin_File: Cookie expiration? Try (re)logging into BBO using your browser.'
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
    print('\nget:', url)
    # todo: use try statement to catch and retry connection errors
    response = session.get(url)
    assert response.status_code == 200, [url, response.status_code] # todo: need to retry error 500?
    assert 'Please login' not in response.text, 'BBO_Download_Lin_Files_Batch: expiration? Try (re)logging into BBO using your browser.'

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
            # todo: use try statement to catch and retry connection errors
            response = session.get(traveller_url)
            assert response.status_code == 200, [
                traveller_url, response.status_code]
            assert 'Please login' not in response.text, 'BBO_Download_Lin_Files_Batch: Cookie expiration? Try (re)logging into BBO using your browser.'
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
            # todo: use try statement to catch and retry connection errors
            response = session.get(tourneyUrl)
            assert response.status_code == 200, [
                tourneyUrl, response.status_code]
            assert 'Please login' not in response.text, 'BBO_Download_Lin_Files_Batch: Cookie expiration? Try (re)logging into BBO using your browser.'
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

    login_url = "https://www.bridgebase.com/myhands/myhands_login.php?t=%2Fmyhands%2Findex.php%3F"
    data = {
        "username": BBO_USERNAME,
        "password": BBO_PASSWORD,
        'keep': True,
    }
    print('post login_url:', login_url)
    response = session.post(login_url, data=data)
    assert response.status_code == 200, [login_url, response.status_code]
    assert 'Please login' not in response.text, 'BBO_login: login failure. Try (re)logging into BBO using your browser.'

    index_url = "http://www.bridgebase.com/myhands/index.php?offset=0"
    print('get index_url:', index_url)
    # todo: use try statement to catch and retry connection errors
    response = session.get(index_url)
    assert response.status_code == 200, [index_url, response.status_code]
    assert 'Please login' not in response.text, 'BBO_login: login failure. Try (re)logging into BBO using your browser.'

    return response


if __name__ == '__main__':

    # initialize global variables
    load_dotenv()

    # Initialize BBO_USERNAME, BBO_PASSWORD. They come from environment variables or from .env file. Requires that you create .env file containing your private values.
    BBO_USERNAME = os.getenv('BBO_USERNAME')
    assert BBO_USERNAME is not None
    BBO_PASSWORD = os.getenv('BBO_PASSWORD')
    assert BBO_PASSWORD is not None

    # Initialize start and end dates of desired downloads. Must be in YYYY-MM-DD format.
    start_date = "2023-01-01"  # user modifyable
    # user modifyable # or "2023-03-31" # todo: check if utc is correct timezone.
    end_date = datetime.now(timezone.utc).date()

    # initialize directory path to where data is to be stored.
    dataPath = pathlib.Path('e:/bridge/data/bbo/data')  # user modifyable
    dataPath.mkdir(parents=True, exist_ok=True)

    print('creating session object')
    session = requests.Session()

    BBO_login(session, BBO_USERNAME, BBO_PASSWORD)

    # read a list of bbo usernames to have their lin files downloaded. Any BBO player can be requested by any other user.
    # lin files will now be downloaded. Files already existing in the local download directory will not be re-downloaded. This makes restarts very quick.

    with open('bbo_usernames.txt','r') as f:
        usernames = f.read().split('\n')

    for username in usernames:  # download lin files of some frequent players
        # perform file downloads for specified date range
        BBO_Download_Lin_Files(session, start_date, end_date, username)

#!/usr/bin/env python
import bs4
import requests

url = "http://pda.5284.com.tw/MQS/businfo2.jsp?routeId={route:d}"


def get_html(route):
    # request page
    res = requests.get(url.format(route=route))
    # check that request was successful - if not, return None - may
    # want to consider throwing an exception here
    if res.status_code != 200:
        return None
    # parse html
    soup = bs4.BeautifulSoup(res.text, "lxml")
    # replace <br> elements with actual spaces
    for br in soup.find_all("br"):
        br.replace_with(" ")
    # get all the tables
    tables = soup.find_all("table")

    # extract all rows from tables 3 and 4, return it as two vectors
    # (for the two directions) each with many (location_name, state)
    # pairs
    return [[[x.text for x in r.find_all("td")]
            for r in t.find_all("tr")]
            for t in tables[3:5]]

if __name__ == "__main__":
    import json
    import time
    # infinite loop!
    while 1:
        # put everything in a try so that we can continue even if
        # things go wrong
        try:
            # get the data for this point in time
            data = get_html(650)
            # make sure request was successful
            if data is not None:
                # save data as json to data folder, putting the route
                # and time in the filename
                json.dump(
                    data,
                    open("data/{}_{:.0f}.json".format(650, time.time()), "w")
                )
            print(time.time(), data)
        except Exception as e:
            print(e)
        # wait 30 seconds before fetching again
        time.sleep(30)

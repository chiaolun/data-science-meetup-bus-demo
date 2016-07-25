#!/usr/bin/env python
import bs4
import requests

url = "http://pda.5284.com.tw/MQS/businfo2.jsp?routeId={route:d}"


def get_html(route):
    res = requests.get(url.format(route=route))
    if res.status_code != 200:
        return None
    soup = bs4.BeautifulSoup(res.text, "lxml")
    for br in soup.find_all("br"):
        br.replace_with(" ")
    tables = soup.find_all("table")

    return [[[x.text for x in r.find_all("td")]
            for r in t.find_all("tr")]
            for t in tables[3:5]]

if __name__ == "__main__":
    import json
    import time
    while 1:
        try:
            data = get_html(650)
            if data is not None:
                json.dump(
                    data,
                    open("data/{}_{:.0f}.json".format(650, time.time()), "w")
                )
            print(time.time(), data)
        except Exception as e:
            print(e)
        time.sleep(30)

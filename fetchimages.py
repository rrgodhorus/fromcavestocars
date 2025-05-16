""" Fetches images for all items the from caves to cars game.  """

import googleimagelib
import pixabayimagelib

import fctcdb

import requests

ITEMDB = None

SEARCHAPI = None

import time

# delay between requests in seconds.   Avoids overwhelming the search api
DELAY_BETWEEN_REQUESTS = 1

REDO = False

FETCHIMAGES = True
PREFIX = "static/images/items/"

import requests

def download_url_to_file(url, filename):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120 Safari/537.36'),
        'Referer': 'https://pixabay.com/'
    }
    resp = requests.get(url, headers=headers, stream=True)
    resp.raise_for_status()  # will raise HTTPError for 4xx/5xx

    with open(filename, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def main():

    # get the itemdb
    global ITEMDB
    ITEMDB = fctcdb.ItemDB(dbfile="itemdb.json")

    # set up the image search engine
    global SEARCHAPI
#    SEARCHAPI = googleimagelib.get_search_api()
    SEARCHAPI = pixabayimagelib.get_search_api()


    for item in ITEMDB.items:

        if not hasattr(ITEMDB.items[item],"image") or REDO:
            # always ask for a primitive version of something (I guess?)
            search_term = item
            if "primitive" not in search_term:
                search_term = "primitive "+item

            print(f"Fetching image for a primitive {item}")
            try:
                result = SEARCHAPI.search_for_image(search_term)
            except requests.exceptions.HTTPError as e:
                print("Retrieval quota exceeded.   Exiting.")
                return

            itemfn = item.replace(" ","_")
            if FETCHIMAGES:
                for index, _image in enumerate(result):
                    # download the image and thumbnail
                    download_url_to_file(result[index]["link"], PREFIX+itemfn + "_"+str(index)+".jpg")
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                    download_url_to_file(result[index]["thumbnailLink"], PREFIX+itemfn +"_"+str(index)+ "_thumb.jpg")
                    time.sleep(DELAY_BETWEEN_REQUESTS)

            for index, _image in enumerate(result):
                result[index]["link"] = PREFIX+itemfn + "_"+str(index)+".jpg"
                result[index]["thumbnailLink"] = PREFIX+itemfn +"_"+str(index)+ "_thumb.jpg"

            # update the database...
            ITEMDB.items[item].image = result

            time.sleep(DELAY_BETWEEN_REQUESTS)

    print("Complete!")

if __name__ == "__main__":
    try:
        main()
    finally:
        ITEMDB.save()
        SEARCHAPI.save_cache()

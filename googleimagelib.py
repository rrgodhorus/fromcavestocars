""" This library provides a simple interface to do a search for images in
Google Image's API.  It has a cache of recent search terms so that it doesn't
repeat requests.   """

import os

import requests

API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_CSE_ID")


def _do_raw_image_search(search_term, num_results):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_term,
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "searchType": "image",
        "safe": "high",
        # JAC: I probably need to look at the license types here in more detail
        # but it seems like public domain only is very safe
        "rights": "cc_publicdomain",
        "num": num_results,  # number of images you want
    }

    response = requests.get(search_url, params=params)
    response.raise_for_status()  # Raise an error if the request failed

    results = response.json()


    images = []
    for item in results.get("items", []):
        image_data = {
            "link": item.get("link"),  # direct image URL
            "contextLink": item.get("image", {}).get("contextLink"),  # page it's from
            "thumbnailLink": item.get("image", {}).get("thumbnailLink"),
            "source": "Google Images",
        }
        images.append(image_data)

    return images


import imagecachelib

def get_search_api():
    """ gets the search API object which caches results...  """
    return imagecachelib.GeneralImageSearchAPI(_do_raw_image_search,"ic.googleimage.json",True)


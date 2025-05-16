""" This library provides a simple interface to do a search for images in
Pixabay's Image API.  It has a cache of recent search terms so that it doesn't
repeat requests.   """

import os

import requests

API_KEY = os.getenv("PIXABAY_API_KEY")

# This site has only public domain images and has very generous search API
# limits, so is a good fit.

def _do_raw_image_search(search_term, num_results):
    search_url = "https://pixabay.com/api/"
    params = {
        "q": search_term,
        "key": API_KEY,
        "safesearch": "true",
        "page": 1,  
        "per_page": num_results  # number of images you want
    }

    response = requests.get(search_url, params=params)

    response.raise_for_status()  # Raise an error if the request failed

    results = response.json()

    # I'm going to parse this to make it have a uniform format...
    images = []
    for item in results.get("hits", []):
        image_data = {
            "link": item.get("previewURL"),  # BUG: I other URLs here that go
                                             # to the site, but I get 400 and
                                             # 403 errors from pixabay.   
                                             # ChatGPT couldn't really help.
                                             # switching to previewURL which 
                                             # goes to their CDN for now...
            "contextLink": item.get("pageURL"),  # page it's from
            "thumbnailLink": item.get("previewURL"),  # thumbnail URL
            "source": "Pixabay",  # source of the image
        }
        images.append(image_data)

    return images


import imagecachelib

def get_search_api():
    """ gets the search API object which caches results...  """
    return imagecachelib.GeneralImageSearchAPI(_do_raw_image_search,"ic.pixabay.json",True)


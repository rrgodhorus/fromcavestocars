""" This library provides a simple interface to do a cache responses from an
Image API.  This avoids the need to repeat requests.   """

import json


from os.path import exists

# TODO: I should probably make this a common class for all of the image APIs...
class GeneralImageSearchAPI:

    def __init__(self,imagesearchfunc,cachefilename,create_if_needed=False):
        self.search_cache = {}
        self.imagesearchfunc = imagesearchfunc
        self.cachefilename = cachefilename
        if not exists(cachefilename) and create_if_needed:
            print(f"Creating cache file {cachefilename}")
            with open(cachefilename, 'w') as f:
                json.dump({}, f)

        # load the cache file...
        with open(cachefilename) as f:
            self.search_cache = json.load(f)

    def save_cache(self):
        if self.cachefilename:
            with open(self.cachefilename, 'w') as f:
                json.dump(self.search_cache, f)

    def search_for_image(self, search_term, num_results=10):
        """ Search for an image using the image API.  If it's been done
        before and is thus cached, return that instead.   """
        if search_term in self.search_cache:
            return self.search_cache[search_term]
        else:
            # Search the image API
            resultlist = self.imagesearchfunc(search_term, num_results)

            self.search_cache[search_term] = resultlist
            self.save_cache()
            return resultlist



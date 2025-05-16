""" This library is the from caves to cars "describer" library.
It takes an item and gets a detailed description which is suitable for the
game.   In particular, the item name itself is not included in the description.
This also gets other rich content for the items, such as an image, a link
to the wikipedia article, etc.

It can be used to describe a tool, raw material, or a step.
"""

from openaiquerylib import join_with_quotes_and_commas

DESCRIPTIONLENGTH = 70
DESCRIPTIONPERITEMLENGTH = 20

class Describer:
    """ This class describes items in the game in a rich way.   It will query
    a source (the OpenAI Query object, image searcher, or wikipedia discovery
    object) and populates the data back into the item database.
    """

    def __init__(self,itemdb, oaiq=None, wikidisc=None, imgsearch=None):
        """ The constructor takes an OpenAI query object, a wikipedia discovery
        object, and an image searcher object.  It also takes an item database
        object.  The itemdb is required since this is effectively the output
        of the object.   Others are optional and will only be used by their
        respective methods.
        """
        self.itemdb = itemdb
        self.oaiq = oaiq
        self.wikidisc = wikidisc
        self.imgsearch = imgsearch


    def describe_item(self, item):
        """ This method takes an item and gets a description of it.  It will
        use the OpenAI query object to get a description of the item.  It will
        also use the wikipedia discovery object to get a link to the wikipedia
        article about the item.  It will also use the image searcher object to
        get an image of the item.  The item is passed in as a string.
        """

        querystring = f"""Please provide a description of how the following item would appear in nature to a primitive human.   Do not describe potential uses for this.  Use the present tense and do not use the name in the description.  Your description should be about {DESCRIPTIONLENGTH} words.   The item is {item}"""

        # Get the description from OpenAI
        if self.oaiq:
            desc = self.oaiq.do_query(querystring)
            if 'sorry' in desc.lower():
                desc = f"Unfortunately, the model refused to describe: {item}"
                #raise ValueError(f"describe_item could not get a description of {item}.")

            self.itemdb.items[item].description = desc


    def describe_step(self, item, stepinfo):
        """ Describes a step involved in making an item."""

        # this doesn't need the itemdb.   It manipulates stepinfo directly

        # Now I will get the description of the step
        querystring = f"""Please provide a description of how a primitive human that is making {item} would do "{stepinfo['step']}".  """ 
        if stepinfo['tools']:
            querystring += f"  The tools used are {join_with_quotes_and_commas(stepinfo['tools'])}.  "
        if stepinfo['raw_materials']:
            querystring += f"  The raw materials used are {join_with_quotes_and_commas(stepinfo['raw_materials'])}.  "
        textlength = DESCRIPTIONLENGTH + (len(stepinfo['tools'])+len(stepinfo['raw_materials']))*DESCRIPTIONPERITEMLENGTH
        querystring += f"""Use the present tense and do not use the word {item} in the description.  Your description should be about {textlength} words."""

        # Get the description from OpenAI
        if self.oaiq:
            desc = self.oaiq.do_query(querystring)
            if 'sorry' in desc.lower():
                desc = f"Unfortunately, the model refused to describe step {stepinfo}"
                #raise ValueError(f"describe_step could not get a description of {item} step {stepinfo}.")

            # Just stick this right into the stepinfo dictionary we were given
            stepinfo['description'] = desc


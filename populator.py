#!/usr/bin/python3
"""
The main thing this library does is when given an item, figure out the 
raw materials and tools / equipment needed to make it.   
This works recursively.

This is effectively an intermediary between the OpenAI API (which is quite
general).  This library contains a bunch of the From Caves To Cars specific 
functionality, while allowing the other library to be more general.

Right now this library focuses on building things from what would be found
in nature by breaking this process down into two parts:

1) Raw Materials: Basic substances needed for production (e.g., wood, metal, fabric).

2) Tools / Equipment: Instruments required to manipulate raw materials (e.g., saws, hammers, machines).

In the future, I may expand this to include the other 3 items (Energy Sources,
Knowledge and Skills, and Time) but for now, I'm just going to focus on
the first two.

My first idea, just get a list of all of these things.   If there is an "OR" or
an optional item, handle these in the simplest way possible.   This means
pick the first item of any OR and drop all optional items.

TODO: Expand on this later to enable different items to be used.
"""

import itertools

import sys # for exit
from os.path import exists

# for colored output
from colorama import Fore, Back, Style

# catch CTRL-C and set a flag so we can exit cleanly...
import signal

# Global flag
CTRL_C_PRESSED = False

def handle_sigint(signum, frame):
    global CTRL_C_PRESSED
    CTRL_C_PRESSED = True
    print("\n[!] Ctrl-C pressed, will exit cleanly...")

# Register handler for Ctrl-C (SIGINT)
signal.signal(signal.SIGINT, handle_sigint)



# the first two lines are what it responds when the LLM has no answer 
# The sorry / help responses come from OpenAI refusing to answer a question
USELESS_RESPONSES = ["none", "no","omit", "omitted", 'empty', "null", "n/a",
        "nothing", "vacant", "blank", "missing", "void", "excluded", 
        'sorry', 'help']

def is_useless_response(response):
    """ This function checks if the response is useless.   This is used to
    filter out responses that are not useful.   For example, if the model
    returns "None" or "(none)" or "no output", this is not useful."""

    # only retain spaces and letters
    filteredresponse = ''.join(c for c in response if c.isalpha() or c.isspace())

    for useless in USELESS_RESPONSES:
        # if it contains a whole word of this type, it is useless
        if useless in filteredresponse.lower().split():
            return True
    return False


# these pop-up in OpenAI responses, despite me asking it to just omit any
# output.   Hence, I'll filter these out.

# This query lib helps to cache queries and do some basic processing
# it is agnostic to the specific needs of From Caves To Cars.
import openaiquerylib

CACHEFILE = "openai.cache.json"

OAIQ = None

# JAC: TODO: actually put all of this stuff into a database

import fctcdb
# This is the database that contains the requested items, toole/equipment, and 
# raw materials.   Each of these is an object with a set of properties.
# The database itself is an object that contains theste and also has methods
# to query properties, save / load, etc..

ITEMDB = None

ITEMDBFILE = "itemdb.json"

import describelib
# how we get detailed descriptions of things...

DESCRIBER = None

def _describe_item_helper(item):
    if DESCRIBER is None:
        return
    if item not in ITEMDB.items:
        # I don't know this
        return
    if hasattr(ITEMDB.items[item],'description') and ITEMDB.items[item].description != "":
        # I already know this
        return

    # get this item
    DESCRIBER.describe_item(item)


def _get_pretty_item_list(itemlist):
    """ This function takes a list of items and colors the items based on 
    their status.  
    """

    prettylist = []
    for item in itemlist:
        prettylist.append(_get_pretty_item_name(item))

    return ", ".join(prettylist)

def _get_pretty_item_name(item):
    if item not in ITEMDB.items:
        return Fore.RESET+f"{item}"+Fore.RESET
    if ITEMDB.items[item].status == "Complete":
        return Fore.CYAN+f"{item}"+Fore.RESET
    elif ITEMDB.items[item].status == "Need to process":
        return Fore.YELLOW+f"{item}"+Fore.RESET
    elif ITEMDB.items[item].status == "In Progress":
        return Fore.GREEN+f"{item}"+Fore.RESET
    else:
        return Fore.MAGENTA+f"{item}"+Fore.RESET

def _get_simple_list(query):
    """ Does a query that retuns a list.  This discards OR and optional items.
    It also splits AND items into separate items.

    In the future, I'll do something more advanced and support these types of
    items."""

    rawresult = OAIQ.do_query(query)

    sanitizedlistresult = openaiquerylib.sanitize_list_output(rawresult)

    # convert to lowercase because sometimes the model changes case
    lowercaseresult = [s.lower() for s in sanitizedlistresult]

    # let's remove optional items
    withoutoptional = openaiquerylib.remove_optional_items_in_list(lowercaseresult)

    # let's remove OR items
    withoutor = openaiquerylib.split_or_items_in_list(withoutoptional)
    
    # if there are multiple items with ORs, take the first and discard the rest.
    withoutorlist = []
    for item in withoutor:
        if type(item) == list:
            item = item[0]
        withoutorlist.append(item)

    # Let's make the "ANDs" their own separate items.
    finallist = openaiquerylib.flatten_and_items_in_list(withoutorlist)

    # This happens if it refuses to explain how to make something, etc.
    if len(finallist) == 1:
        if is_useless_response(finallist[0]):
            # if the result is useless, return an empty list
            return []

    return finallist


PRIMITIVE_AGE_FOR_ALL = False

def is_younger(year1: str, year2: str) -> bool:
    def parse_year(s: str) -> int:
        s = s.strip().upper()

        # remove dates with a comma
        s = s.replace(',','')

        if s.endswith("BCE"):
            year_part = s[:-3].strip()
            if not year_part.isdigit():
                raise ValueError(f"Invalid year format: '{s}'")
            return -int(year_part)
        elif s.endswith("BC"):
            year_part = s[:-2].strip()
            if not year_part.isdigit():
                raise ValueError(f"Invalid year format: '{s}'")
            return -int(year_part)
        elif s.endswith("AD"):
            year_part = s[:-2].strip()
            if not year_part.isdigit():
                raise ValueError(f"Invalid year format: '{s}'")
            return int(year_part)
        elif s[-1].isdigit():
            # Assume AD if no era given
            if not s.isdigit():
                raise ValueError(f"Invalid year format: '{s}'")
            return int(s)
        else:
            raise ValueError(f"Invalid era in year: '{s}'")

    return parse_year(year1) <= parse_year(year2)


def get_item_age(item):
    """ This returns an estimated age for an item"""

    querystring = '''Roughly what year was the first human made "'''+item+'''" created?   Only list a year and do not list a range.  Use the year according to the Gregorian calendar and append AD or BCE.  For example: 
4000 BCE'''
    result = OAIQ.do_query(querystring)
    return result


def age_statement(agerestriction=None):
    if not agerestriction:
        return ""
    return f"Ensure everything existed at {agerestriction}, but ideally as old as is possible."


def get_steps_needed_to_make_item(item,agerestriction=None):
    """ gets the steps only needed to make an item."""
#    querystring = '''What are the steps needed for a human to directly make or acquire '''+item+'''?   give a complete list.   Do not list any raw materials, tools/equipment, energy sources, knowledge/skills, or time requirements.   The output should list the step number (in order) and then the step name, with each step on a new line.  If a step is optional add "- optional" to that line.   For example, if asked to give the steps to make a sandwich, you might reply: "1. Gather Ingredients
#2. Prepare Work Area
#3. Slice Bread
#4. Spread Condiments - optional
#5. Add Fillings
#6. Season - optional
#7. Top with Bread
#8. Cut Sandwich - optional
#9. Serve"'''

    querystring = f'''What are the steps needed for a human to directly make or acquire a primitive "{item}" - meaning the item absolutely cannot be made without this step?   give a complete list.   Do not list any raw materials, tools/equipment, energy sources, knowledge/skills, or time requirements.   Do not list any optional steps.   Use the bare minimum steps necessary.   Avoid adjectives unless necessary.   State the name of a step simply, without using any parenthesis or dashes.   Use the simplest set of steps possible, as this item could have been made using the most primitive tools possible. {age_statement(agerestriction)} The output should list the step number (in order) and then the step name, with each step on a new line.''' 

    return _get_simple_list(querystring)


def get_tools_needed_for_step(step,item,agerestriction=None):
#    querystring = '''For step '''+step+''' needed to make '''+item+''', what are the tools/equipment needed?   Give a complete list.   Do not list any raw materials, energy sources, knowledge/skills, or time requirements.   The output should list each tool on a separate line.  If a step is optional add "- optional" to that line. For example, if asked to give the tools/equipment to slice bread as part of making a sandwich, you might reply: "1. Bread Knife
#2. Cutting Board
#3. Bread Slicing Guide - optional
#4. Bread Loaf Wrap - optional"'''
    querystring = f'''For the step "{step}" needed to make "{item}", what are the simplest tools or equipment absolutely required to perform the step — meaning the step cannot be done at all without them? Do not include tools that are merely helpful or make the process easier. Only list tools that are strictly necessary. Exclude raw materials, energy sources, knowledge/skills, and time. {age_statement(agerestriction)} If the step can be done entirely without tools, do not list anything.  Succinctly, list each tool alone on a separate line.  Do not use adjectives or explain the purpose of a tool.'''
#    querystring = '''For step '''+step+''' needed to make '''+item+''', what are the tools/equipment needed?   Give a complete list.   Do not list any raw materials, energy sources, knowledge/skills, or time requirements.   Do not list any optional tools.  Use the bare minimum tools, if any.  If a step can be done wihout tools, do not list any tools.   Avoid adjectives unless needed.   State the name of each tool simply, without using any parenthesis or dashes.  Make sure each tool is a primitive version made from primitive components.  '''+age_statement(agerestriction)+''' The output should list each tool on a separate line. For example, if asked to give the tools/equipment to slice bread as part of making a sandwich, you might reply: "1. Bread Knife
#2. Cutting Board'''

    return _get_simple_list(querystring)


def get_raw_materials_needed_for_step(step,tool,item, agerestriction=None):
    querystring = '''When using tool "'''+tool+'''" with step "'''+step+'''" needed to make "'''+item+'''", what raw materials are needed?   Give a complete list.   Do not list any tools/equipment, energy sources, knowledge/skills, or time requirements.   Do not list any optional raw materials. Use the bare minimum raw materials, if any.  Avoid adjectives unless needed.  State the name of each raw material simply, without using any parenthesis or dashes.  Each raw material should be the simplest item one could use to make this, as would have been used the first time this raw material was used. '''+age_statement(agerestriction)+''' The output should list each raw material on a separate line.  Do not list raw materials used in other steps.  For example, if asked "when using tool Knife with step Slice Bread needed to make a sandwich", you might reply: "Bread"'''

    return _get_simple_list(querystring)


def _true_false_omitted_helper(itemlist,result):
    """ This function is used to process the results of a query that returns
    True or False.   It will return a tuple with three lists.   The first list
    is the items that are True, the second list is the items that are False,
    and the third list is the items that were omitted."""

    truelist = []
    falselist = []
    omittedlist = []
    for item in itemlist:
        # make this lowercase because sometimes the model changes case
        item=item.lower()

        if item in result:
            if len(result[item]) == 0 or len(result[item][0].split()) == 0:
                omittedlist.append(item)
                continue

            if result[item][0].split()[-1] == "True":
                truelist.append(item)
                continue
            elif result[item][0].split()[-1] == "False":
                falselist.append(item)
                continue
        omittedlist.append(item)

    return truelist,falselist,omittedlist

def are_items_natural(itemlist):
    """ This function returns the non-natural items from a list of items.
    A non-natural item is something that is made by humans.   For example,
    a car is not a natural item, but wood is.   This function will return
    a tuple with three lists.   The first list is the items that are natural
    and the second list is the items that are not natural.  The final list 
    is the items that were omitted."""

    result = OAIQ.do_query_with_list_arguments('''Which of the following are natural items?''',itemlist,'''Please list one item per line and respond with True or False for each item.   If the item is not a natural item, please list it. For example:
"car port" False
"wood" True''')

    return _true_false_omitted_helper(itemlist,result)


def are_items_part_of_a_larger_item(itemlist):
    """ This function is meant to filter out items that are not a part of a 
    larger item.  For example, a branch is a part of a tree, but a stone is 
    a derived item.   This function returns a tuple with three lists.   The 
    first list is the items that are derived and the second list is the items 
    that are not derived.  The final list is the items that were omitted"""

    result = OAIQ.do_query_with_list_arguments('''Which of the following are parts of a larger item?''',itemlist,'''Please list one item per line and respond with True or False for each item.   If the item is not a part of a larger item, please list it. For example:
"car door" True
"branch" True
"wood" False''')

    return _true_false_omitted_helper(itemlist,result)


# TODO: refactor tool information into a separate module / class
import json

MAXKNOWNTOOLSPERSTEP = 30
TOOLDICT = {}
KNOWNTOOLS = set()

TOOLFILENAME = "tooldict.json"


def _handled_polyonymous_result(tool, result):
    """ This is a helper that just checks for a single tool in the result 
    and adds it, if needed. """

    global TOOLDICT
    global KNOWNTOOLS

    # no response.   It didn't know.
    if len(result.splitlines()) == 0:
        return False

    # too many results...
    if len(result.splitlines()) >1:
        print(f"Error: {tool} returned multiple lines: {result}.  Skipping.")
        return False

    line = result.splitlines()[0]
    line = line.strip()
    # Sometimes the model uses fancy quotes.   Let's replace them with
    # normal quotes.
    line = line.replace('\u201c','"')
    line = line.replace('\u201d','"')

    if len(line.split('"'))!= 5:
        print(f"Error: {line} doesn't have 4 quotes.  Skipping.")
        return False

    if line.split('"')[0] != '' or line.split('"')[4] != '' or line.split('"')[2] != ' ':
        print(f"Error: '{line}' is malformed.  Skipping.")
        return False

    originaltool = line.split('"')[1]
    equivalenttoolname = line.split('"')[3]
    if originaltool != tool:
        print(f"Error: On '{line}' {originaltool} is not {tool}.  Skipping.  DEBUG:{KNOWNTOOLS}")
        return False

    # didn't find a match, add it as itself.
    if "None" in equivalenttoolname: # I think it should be equal, not "in"
        return False

    # matched something not in the DB.   Print an error...
    elif equivalenttoolname not in KNOWNTOOLS:
        print(f"Error: On '{line}' querying for {tool}: {newtoolname} not in TOOLDICT.  Skipping.")
        return False

    else:
        # I know the tool and what it maps to.   Add it!

        TOOLDICT[tool] = equivalenttoolname

        # We did it!
        return True



def standardize_polyonymous_tooldict(tools):
    """ This function takes a list of tools and a list of knowntools and 
    ensures that a tool isn't already in the knowntools list under a different
    name. """

    # I'm assuming that multiple tools in this list aren't polyonymous.

    # technically I shouldn't need to do this because I'm accessing fields
    # of these, but I'll add this for clarity
    global TOOLDICT
    global KNOWNTOOLS

    uncheckedtools = []
    for tool in tools:
        if tool in TOOLDICT:
            write_verbose_output(Fore.CYAN+f"    {tool} is a known key in the tool dictionary.  Skipping."+Fore.RESET,loglevel=1)
            continue
        if tool in TOOLDICT.values():
            write_verbose_output(Fore.MAGENTA+f"    {tool} is a known value in the tool dictionary.  Skipping."+Fore.RESET,loglevel=1)
            continue
        if tool in KNOWNTOOLS:
            write_verbose_output(Fore.MAGENTA+f"    {tool} is in KNOWNTOOLS.  Skipping."+Fore.RESET,loglevel=1)
            continue
        uncheckedtools.append(tool)

    if uncheckedtools == []:
        return

    tools = uncheckedtools

    # I don't know any tools yet (empty set)
    if not KNOWNTOOLS:
        for tool in tools:
            TOOLDICT[tool] = tool
            KNOWNTOOLS.add(tool)
        return


    for tool in tools:
        it = iter(KNOWNTOOLS)
        while True:
            batch = list(itertools.islice(it, MAXKNOWNTOOLSPERSTEP))

            if not batch:
                # I ran out of things to check.   It's not in the list...
                # ...so add it!
                KNOWNTOOLS.add(tool)
                TOOLDICT[tool] = tool
                break

            batch.append("None")

            querystring = f'''Suppose I have the following tool: {"tool"}.  This tool name is a single item, even if it contains spaces.  Does this tool serve the same purpose as any of the following tools: {openaiquerylib.join_with_quotes_and_commas(batch)}? If so, output original tool name and the replaced tool from the tool list, if needed.  If you do not have a match, produce no output.   For example, if the tool is "hammer"  and the tool list is "a mallet", "a screwdriver", and "None", you would reply: "hammer" "a mallet" Always include the double quotes around the items.'''

            result = OAIQ.do_query(querystring)

            # check each tool and set it up in the database (possibly mapping it
            # to an existing tool)
            if _handled_polyonymous_result(tool, result):
                # I found a match, so break out of the loop and do the next
                #tool
                break

            # The "else" is in the "if not batch:", above.


            




def _create_items_helper(itemlist):
    """ This function is used to create items in the database.   It takes a
    list of items and creates them in the database.   It also sets the status
    to unknown.   This is used to create items that are not in the database.
    """

    # let's track which items we need to work on.   Items in the database don't
    # need to be worked on.
    list_to_make = []
    for item in itemlist:
        if item in ITEMDB.items and ITEMDB.items[item].status == "Complete":
            write_verbose_output(Fore.CYAN+f"    {item} was processed and is being skipped."+Fore.RESET,loglevel=1)
        elif item in ITEMDB.items and ITEMDB.items[item].status == "In Progress":
            # avoid infinite recursion...
            write_verbose_output(Fore.CYAN+f"    {item} is already in progress.  "+Fore.RED+"RECURSIVE LOOP!"+Fore.CYAN+"  Skipping."+Fore.RESET,loglevel=1)
        else:
            ITEMDB.items[item] = fctcdb.GenericItem(item)
            ITEMDB.items[item].status = "Need to process"
            list_to_make.append(item)

    
    tlist, flist, olist = are_items_part_of_a_larger_item(list_to_make)

    for item in list_to_make:
        if item in tlist:
            ITEMDB.items[item].is_part_of_a_larger_item = True
        elif item in flist:
            ITEMDB.items[item].is_part_of_a_larger_item = False
        elif item in olist:
            write_verbose_output(f"Item {item} omitted from is_part_of_a_larger_item",loglevel=1)
            ITEMDB.items[item].is_part_of_a_larger_item = None
        else:
            raise ValueError(f"Item {item} isn't part of a larger item or not.")
    
    tlist, flist, olist = are_items_natural(list_to_make)
    for item in list_to_make:
        if item in tlist:
            ITEMDB.items[item].is_natural = True
        elif item in flist:
            ITEMDB.items[item].is_natural = False
        elif item in olist:
            write_verbose_output(f"Item {item} omitted from is_natural",loglevel=1)
            ITEMDB.items[item].is_natural = None
        else:
            raise ValueError(f"Item {item} isn't natural or not.")


    retlist = []
    for item in list_to_make:
        # if it's something a primitive human could find in nature, then 
        # let's stop.   There isn't anything to do.
        if ITEMDB.items[item].is_base_item():
            ITEMDB.items[item].status = "Complete"
            ITEMDB.items[item].user_requested = False
            write_verbose_output(Fore.YELLOW+f"    {item} is a base item."+Fore.RESET,loglevel=1)
            # I may need to describe this...
            _describe_item_helper(item)
        else:
            ITEMDB.items[item].status = "Need to process"
            retlist.append(item)

    ITEMDB.save()

    return retlist


def query_how_to_make_item(querystring,userrequested):
    """ This figures out how to make an item.   It will use a recursive helper
    function to figure this out for items beneath it.
    Set userrequested to None if you don't want to alter an existing element
    (if it exists).  Otherwise, you'll overwrite the userrequested field"""

    try:
        if querystring in ITEMDB.items and ITEMDB.items[querystring].status == "Complete":
            write_verbose_output(Fore.GREEN+f"Already know about {querystring}.  Skipping."+Fore.RESET,loglevel=1)
            # if I already know about this item, just return
            return 

        if _create_items_helper([querystring]) == []:
            assert(querystring in ITEMDB.items and ITEMDB.items[querystring].status == "Complete")
            # if I don't need to do anything, just return
            write_verbose_output(Fore.YELLOW+f"{querystring} occurs in nature and doesn't need to be processed.  Skipping."+Fore.RESET,loglevel=1)
            return

    finally:
        # indicate that this item was user requested as is indicated.  
        # usually, this will be set, unless we're rebuilding a corrupted 
        # database.
        if userrequested is not None: 
            ITEMDB.items[querystring].user_requested = userrequested
        estimated_age = get_item_age(querystring)
        ITEMDB.items[querystring].estimated_age = estimated_age 

    ITEMDB.items[querystring].status = "Need to process"

    _how_to_make_item_recursively_helper(querystring,agerestriction=estimated_age)



def _how_to_make_item_recursively_helper(querystring, agerestriction=None):
    """
    In this function, we will get the steps needed to make an item.   For
    each step, we will get the raw materials and tools needed.   Then we will
    recursively call this function on the raw materials and tools.
    """

    if agerestriction:
        write_verbose_output(Fore.GREEN+f"Processing {querystring} ({agerestriction})"+Fore.RESET,loglevel=1)
    else:
        write_verbose_output(Fore.GREEN+f"Processing {querystring} (no time restrictions)"+Fore.RESET,loglevel=1)


    # I'll use a status field in the item to indicate if it is completely 
    # studied or not.   I'll also indicate if it's in progress.

    # first, I want to prevent infinite loops (from items appearing as a 
    # tool needed to make themselves).   I also want to prevent re-doing items
    # that I already know about.
    if querystring in ITEMDB.items and ITEMDB.items[querystring].status != "Need to process":
        write_verbose_output(Fore.CYAN+f"  Already know about {querystring} with status {ITEMDB.items[querystring].status}.  Skipping."+Fore.RESET,loglevel=1)

        # describe everything in a rich manner (if needed)
        _describe_item_helper(querystring)

        return

    if ITEMDB.items[querystring].status == "Need to process":
        # I'm processing it.   Prevent recursing into this again.
        ITEMDB.items[querystring].status = "In Progress"

    # Get the steps needed to make the item
    steps = get_steps_needed_to_make_item(querystring,agerestriction)

    stepdata = []

    # These are the things I'll need to work on after.
    itemstoprocess = set([])

    # For each step, get the raw materials and tools needed
    for step in steps:
        write_verbose_output(Fore.RESET+f"  Step: "+Fore.RESET+f"{step}",loglevel=1)

        # Get the tools and raw materials needed for the step
        tools = get_tools_needed_for_step(step,querystring,agerestriction)

        for tool in tools:
            # drop junk responses like None and (no response)
            if is_useless_response(tool):
                tools.remove(tool)

        write_verbose_output(Fore.RESET+f"    Unfiltered Tools: "+Fore.RESET+f"{_get_pretty_item_list(tools)}",loglevel=1)


        # Note, standardize_polyonymous_tooldict doesn't do a list query, so 
        # it will ask over and over again, even if the tool is already known.
        # To avoid that I will filter out tools I've seen first...



        # If I don't filter tools, I end up with 20 variations of a hammer,
        # etc. So I want to filter if there is already an equivalent, known 
        # tool

        # BUG: I am going to make the dubious assumption that the tool's 
        # intended use is not relevant to determining equivalence.   In other
        # words, a hammer and a mallet are either always able to do the same 
        # task or are never able to.

        standardize_polyonymous_tooldict(tools)

        revisedtools = []
        for tool in tools:
            if tool in TOOLDICT:
                if TOOLDICT[tool] != tool:
                    write_verbose_output(Fore.MAGENTA+f"      Substitute {TOOLDICT[tool]} for {tool}."+Fore.RESET,loglevel=1)
                revisedtools.append(TOOLDICT[tool])
            else:
                revisedtools.append(tool)

        itemstoprocess.update(revisedtools)

        # TODO: Fix this later for situations with tools that involve OR
        # For now, assume you need all tools.   This handles things like mortar
        # and pestle or something like hammer and chisel.
        raw_materials = get_raw_materials_needed_for_step(step," and ".join(tools),querystring,agerestriction)

        for material in raw_materials:
            # drop junk responses like None and (no response)
            if is_useless_response(material):
                raw_materials.remove(material)

        itemstoprocess.update(raw_materials)
        write_verbose_output(Fore.RESET+f"    Raw materials: "+Fore.RESET+f"{_get_pretty_item_list(raw_materials)}",loglevel=1)

        stepdata.append({'step':step,'tools':revisedtools,'raw_materials':raw_materials})

    # add my step data to the item
    ITEMDB.items[querystring].steps = stepdata

    for step in stepdata:
        if DESCRIBER and 'description' not in step or step['description'] == "":
            DESCRIBER.describe_step(querystring,step)

    # describe everything in a rich manner (if needed)
    for item in itemstoprocess:
        _describe_item_helper(querystring)

    # Okay, let's create the basic database entries we need for the new tools 
    # and materials
    items_to_make = _create_items_helper(itemstoprocess)

    if items_to_make == []:
        # if I don't need to do anything, just return
        write_verbose_output(Fore.CYAN+f"  No items to make!."+Fore.RESET,loglevel=1)
    else:
        write_verbose_output(f"  Items to make: {_get_pretty_item_list(items_to_make)}"+Fore.RESET,loglevel=1)

    for item in items_to_make:
        ITEMDB.items[item].user_requested = False
        # recursively call this function on the tools and raw materials

        agetouse = agerestriction
        # I can either make this item in the most primitive way or
        # use the tools available at the time of the main query item
        global PRIMITIVE_AGE_FOR_ALL
        if PRIMITIVE_AGE_FOR_ALL:
            new_item_age = get_item_age(item)
            ITEMDB.items[querystring].estimated_age = new_item_age
            if is_younger(agerestriction,new_item_age):
                write_verbose_output(Fore.RED+f"    WARNING: {item} ({new_item_age}) is younger than {querystring} ({agerestriction}).  Using {agerestriction} instead."+Fore.RESET,loglevel=1)
            else:
                agetouse = new_item_age

        _how_to_make_item_recursively_helper(item,agerestriction=agetouse)

    # mark the tools as such
    for step in stepdata:
        for tool in step['tools']:
            ITEMDB.items[tool].is_tool = True

    # describe everything in a rich manner (if needed)
    _describe_item_helper(querystring)

    # I've finished this!
    ITEMDB.items[querystring].status = "Complete"
    write_verbose_output(Fore.GREEN+f"Finished processing {querystring}."+Fore.RESET,loglevel=1)

    persiststores()





LOGLEVEL = 0

def write_verbose_output(information,loglevel,end="\n"):
    if loglevel <= LOGLEVEL:
        print(information,end=end)


def persiststores():
    """ This function is used to persist the database and cache files (usually
    before exiting). """

    # Save the database
    ITEMDB.save()

    # Save the cache file
    OAIQ.write_cache_to_disk()

    # save the tool files
    tooldata = {
        'TOOLDICT': TOOLDICT,
        'KNOWNTOOLS': list(KNOWNTOOLS)
    }
    json.dump(tooldata, open(TOOLFILENAME, "w"), indent=4)
    
    if CTRL_C_PRESSED:
        write_verbose_output(Fore.RED+f"CTRL-C pressed.  Exiting."+Fore.RESET,loglevel=0)
        sys.exit(1)


# this parses command line arguments including either a command line option
# of the item one is trying to build, or a file containing a list of items to 
# build.
import argparse

defaultconfig = {
    "querystring": None,
    "queryfile": None,
    "rebuild": 0,
    "ignorecorruption": False,
    "verbose": 0,
    "describe": False,
    "primitiveageforall": False
}

def main():

    CONFIGFILE = "config.json"

    config = {}
    if exists(CONFIGFILE):
        # load in the configuration file with the default settings
        with open(CONFIGFILE) as f:
            config = json.load(f)

    merged_config = {**defaultconfig, **config}

    config_namespace = argparse.Namespace(**merged_config)

    # Define the version number
    VERSION = "1.0.0"

    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="From Caves To Cars Game - Populator.  Queries the LLM to get the raw materials and tools needed to build an item.",
        usage="%(prog)s [options]"
    )

    # Add the query string argument
    parser.add_argument(
            "-q", "--querystring",
            type=str,
            help="The item you want to build"
        )

    # I only make the main item with tools older than it.   Should other
    # items be made with tools that are as old as the main item or should
    # they use the age of the tool they are building?
    parser.add_argument(
            "-p", "--primitiveageforall",
            action="store_true",
            help="When making an item, do I use the most primitive version of each tool possible?"
        )

    # Add the query file argument
    parser.add_argument(
            "-f", "--queryfile",
            type=str,
            help="A file containing a list of items to build (one per line)"
        )

    # Add an option to rebuild the database.   
    parser.add_argument(
            "-r", "--rebuild",
            action="count",
            help="Rebuild the database from scratch (use -rr to reprocess each item)"
        )

    # Add an option to ignore corruption
    parser.add_argument(
            "-i", "--ignorecorruption",
            action="store_true",
            help="Ignore corruption in the database"
        )

    # Add the verbose argument
    parser.add_argument(
            "-v", "--verbose",
            action="count",
            help="Enable increasingly verbose output (with more -vvvv options)"
        )

    # Add the verbose argument
    parser.add_argument(
            "-d", "--describe",
            action="store_true",
            help="Describe items and steps."
        )

    # Add a version argument
    parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {VERSION}",
            help="Show the version number and exit"
        )

    # Parse the arguments
    args = parser.parse_args(namespace=config_namespace)
    querylist = []

    with open(CONFIGFILE, "w") as f:
        # Save the configuration file with the default settings
        json.dump(vars(args), f, indent=4)

    global PRIMITIVE_AGE_FOR_ALL
    PRIMITIVE_AGE_FOR_ALL = args.primitiveageforall

    global LOGLEVEL
    LOGLEVEL = args.verbose

    if args.querystring:
        # If a query string is provided, use only it
        querylist = [args.querystring]

    elif args.queryfile:
        # Otherwise, read from the file
        with open(args.queryfile, "r") as f:
            querylist = [line.strip() for line in f.readlines()]

    # If no query string or file is provided, print an error message
    if not querylist and not args.rebuild:
        print("No action provided. Use -h for help.")
        return

    write_verbose_output(Fore.YELLOW+f"Loading saved database state..."+Fore.RESET,loglevel=0)
    # initialize the OpenAI query library
    # I made this global, but I could have made this function have an object
    # which contains the OpenAIQuery object.
    global OAIQ
    OAIQ = openaiquerylib.OpenAIQuery(cachefile=CACHEFILE,model = "o4-mini-2025-04-16",create_if_needed=True)

    #load the From Caves To Cars item database
    global ITEMDB
    ITEMDB = fctcdb.ItemDB(dbfile=ITEMDBFILE, create_if_needed=True)

    global DESCRIBER
    if args.describe:
        # need to add wiki and image describers
        DESCRIBER = describelib.Describer(ITEMDB,OAIQ)

    # load the tool information...
    if not exists(TOOLFILENAME):
        write_verbose_output(Fore.YELLOW+f"No saved tool data..."+Fore.RESET,loglevel=0)
        # if the file doesn't exist, create it
        tooldata = {
            'TOOLDICT': {},
            'KNOWNTOOLS': set([])
        }
    else:
        tooldata = json.load(open(TOOLFILENAME, "r"))

    global TOOLDICT
    global KNOWNTOOLS
    TOOLDICT = tooldata['TOOLDICT']
    KNOWNTOOLS = set(tooldata['KNOWNTOOLS'])


    # First, check if the database needs to be rebuilt.
    # all items in the database should be complete (or else it crashed in the
    # middle of processing)
    corrupteditems = ITEMDB.filter_items(lambda x: x.status != "Complete")
    if corrupteditems != []:
        print(f"The database contains {len(corrupteditems)} incomplete items and is likely corrupted.")
        if not args.rebuild and not args.ignorecorruption:
            print("Exiting  Use -r to rebuild the database.")
            return

    if args.rebuild:
        if args.rebuild > 1:
            print(f"Rebuilding ALL {len(ITEMDB.items)} items in the database.")
            # make this all database items
            corrupteditems = ITEMDB.filter_items(lambda x: True)
            for item in ITEMDB.items:
                ITEMDB.items[item].status = "Need to process"
        else: # only rebuild legitimately corrupted items
            print(f"Rebuilding {len(corrupteditems)} items in the database.")
            for item in corrupteditems:
                # change any that are marked as In Progress so they get actually
                # processed instead of skipped (essentially this clears the flag
                # which says this is recursively being processed)
                if ITEMDB.items[item].status == "In Progress":
                    ITEMDB.items[item].status = "Need to process"

        for item in corrupteditems:
            write_verbose_output(Fore.MAGENTA+f"REPAIRING: {item}:"+Fore.RESET,loglevel=0)
            # Do the query
            query_how_to_make_item(item,userrequested=None)

    try:
        for query in querylist:
            # Explain what you are querying for
            write_verbose_output(Fore.MAGENTA+f"MAIN QUERY: {query}"+Fore.RESET,loglevel=0)

            # Do the query
            query_how_to_make_item(query, userrequested=True)

            # Newline for better readability
            write_verbose_output("",loglevel=1)
    finally:

        # Clean up before exiting
        persiststores()



if __name__ == "__main__":
    main()

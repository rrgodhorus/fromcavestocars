#!/usr/bin/python3
import openaiquerylib

# I'll do some basic testing, mostly integration tests, but I will poke into
# internals in a few places if I really need to.   I'll cache results
# unless I'm told not to.

import sys





def setup(args):
    flush = False
    cachefile = "testcache.json"
    nocache = False

    usagestring = """
    Usage: test_openaiquerylib.py [--flush] [--nocache]

    runs the unit tests for the openaiquerylib.   
    --flush    removes any existing cache data and starts a new cache
    --nocache  does not use a cache on this run 
    """

    for arg in args:
        if arg == '--flush':
            flush = True
        elif arg == '--nocache':
            nocache = True
        elif arg == '--help':
            print(usagestring)
            sys.exit(1)
        else:
            print("Unknown argument: '",arg,"'")
            print()
            print(usagestring)
            sys.exit(1)
        


    if flush:
        oaiq = openaiquerylib.OpenAIQuery(None)
        oaiq.empty_cache()
        oaiq.fully_enable_cache(cachefile)
        oaiq.write_cache_to_disk()
    else:
        oaiq = openaiquerylib.OpenAIQuery(cachefile)

    if nocache:
        oaiq.fully_disable_cache()

    return oaiq


def main():
    oaiq = setup(sys.argv[1:])

    # Will raise an exception (and fail the test) if this isn't in the answer.
    oaiq.do_query("Who are the main actors in the movie Monty Python's Quest For the Holy Grail?").index("Eric Idle")


    result = oaiq.do_query_with_list_arguments("Which of the following are vegetables:", ['carrot', 'banana', 'cow'], """List one item per line and the word 'True' or 'False' after the item.   For example: 
horse False
cabbage True""")

    assert len(result['carrot']) == len(result['banana']) == len(result['cow']) == 1
    assert len(result) == 3
    assert 'True' in result['carrot'][0]
    assert 'False' in result['banana'][0]
    assert 'False' in result['cow'][0]


    result = oaiq.do_query_with_list_arguments("Which of the following are vegetables:", ['banana', 'radish','cow', 'cat'], """List one item per line and the word 'True' or 'False' after the item.   For example: 
horse False
cabbage True""")

    assert len(result['banana']) == len(result['radish']) == len(result['cat']) == len(result['cow']) == 1
    assert len(result) == 4
    assert 'False' in result['banana'][0]
    assert 'False' in result['cow'][0]
    assert 'True' in result['radish'][0]
    assert 'False' in result['cat'][0]

    # peek into the data structure to see if we can understand if it repeated
    # parts of the query it shouldn't have.

    for querystring in oaiq.cache['raw']:
        if 'Which of the following are vegetables:' in querystring:
            if 'radish' in querystring and 'cow' in querystring:
                print("do_query_with_list_arguments did not cache results: '"+querystring+"'")

    # Do queries that do not update the knowledge base

    assert oaiq.do_query_which_returns_unambiguous_ordered_list("List the wives of Henry VIII from oldest to youngest at their time of marriage.  Be concise.", "Do not list any information other than the names") == ['Catherine of Aragon', 'Anne Boleyn', 'Jane Seymour', 'Anne of Cleves', 'Catherine Howard', 'Catherine Parr']

    # test parsing / manipulation functions...

    assert(openaiquerylib.split_or_items_in_list(['Alice', 'Bob or Sue or Jane', 'Tom, Dick, or Harry', 'Charlie']) ==   ['Alice', ['Bob', 'Sue', 'Jane'], ['Tom', 'Dick', 'Harry'], 'Charlie'])

    assert(openaiquerylib.remove_optional_items_in_list(['Alice', 'Bob (optional)', 'Tom', 'Charlie (optional)']) == ['Alice','Tom'] )

    assert(openaiquerylib.flatten_and_items_in_list( ['Alice', 'Bob and Sue or Jane', 'Amy, Barb, or Beth', 'Tom, Dick, and Harry', 'Charlie']) == ['Alice', 'Bob', 'Sue or Jane', 'Amy, Barb, or Beth', 'Tom', 'Dick', 'Harry', 'Charlie'])


    assert(openaiquerylib.create_uniform_dictionary_from_resultlist([ "apple True", "banana False"]) == {'apple': True, 'banana': False})

    assert(openaiquerylib.create_uniform_dictionary_from_resultlist([ "apple 2", "banana 9", "date 5", "asjkfd 3"]) == {'apple': 2, 'banana': 9, 'date': 5, 'asjkfd': 3})

    assert(openaiquerylib.create_uniform_dictionary_from_resultlist([ "apple 2.0", "banana 9", "date 5", "asjkfd 3"]) == {'apple': 2.0, 'banana': 9.0, 'date': 5.0, 'asjkfd': 3.0})

    assert(openaiquerylib.create_uniform_dictionary_from_resultlist([ "apple 42", "banana 3.14", "date", "asjkfd"]) == {'apple': '42', 'banana': '3.14', 'date': '', 'asjkfd': ''})


    # wipe out the kb, which may have data from a prior run.
    oaiq.kb_flush()

    # Do queries that update the knowledge base

    try:
        oaiq.kb_list_update("new val", "This query string was never performed")
    except ValueError:
        pass
    else:
        raise AssertionError("kb_list_update failed to error on an unknown querystring")

    # add this query to the knowledge base...
    oaiq.kb_list_update("is veg", "Which of the following are vegetables:", ['carrot'])

    assert(oaiq.cache['kb']['is veg']['carrot'] is True)

    try:
        oaiq.cache['kb']['is veg']['banana']
    except KeyError:
        pass
    else:
        raise AssertionError("kb_list_update failed to selectively update")
    
    # let's add them all!
    oaiq.kb_list_update("is veg", "Which of the following are vegetables:")
    assert(not oaiq.cache['kb']['is veg']['banana'])


    result = oaiq.kb_list_query("num legs","How many legs do these creatures have?", ['cow', 'snake', 'squid'], """List one item per line and the number after the item.  The answer should only say the creature name and the number with no other output.    For example: 
cat 4
octopus 8
snail 1
""")

    assert '4' in result['cow'][0]
    assert(oaiq.cache['kb']['num legs']['cow'] == 4)
    assert(oaiq.cache['kb']['num legs']['snake'] == 0)
    assert(oaiq.cache['kb']['num legs']['squid'] == 10)

    # let's flush the kb for one item...
    oaiq.kb_flush("is veg")

    try:
        oaiq.cache['kb']['is veg']['banana']
    except KeyError:
        pass
    else:
        raise AssertionError("kb_flush failed to remove key")

    assert(oaiq.cache['kb']['num legs']['cow'] == 4) # should still be there

    try:
        oaiq.kb_flush("not a real key")
    except KeyError:
        pass
    else:
        raise AssertionError("Should have errored when flushing a non-existent key")
        



if __name__ == "__main__":
    main()

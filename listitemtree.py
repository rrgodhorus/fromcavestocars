# this prints out a treelike structure of the items in the itembd for the
# caves to cars project.

from colorama import Fore, Back, Style

import fctcdb
ITEMDB = None

ITEMDBFILE = "itemdb.json"

import sys

SEEN = []
COUNTS = {}

def print_step(itemdb, stepdict, prefix=''):

    raw_materials = stepdict.get('raw_materials', [])
    tools = stepdict.get('tools', [])

    items = list(raw_materials + tools)
    count = len(items)

    for i, key in enumerate(items):
        connector = '└── ' if i == count - 1 else '├── '
        if key in SEEN:
            last = Fore.YELLOW+' (seen)'+Fore.RESET
            COUNTS['duplicates'] += 1
        else:
            last = ''

        if key in raw_materials:
            print(prefix + connector + Fore.CYAN+key+last+Fore.RESET)
            COUNTS['raw_materials'] += 1
        else:
            print(prefix + connector + Fore.BLUE+key+last+Fore.RESET)
            COUNTS['tools'] += 1

        extension = '    ' if i == count - 1 else '│   '
        # don't recurse if we've seen it to prevent infinite loops
        if key not in SEEN:
            print_item(itemdb, key, prefix + extension)



def print_item(itemdb, requesteditem, prefix=''):

    SEEN.append(requesteditem)
    thisitem = itemdb.items[requesteditem]
    stepdicts = getattr(thisitem,'steps', [])
    steps = []
    for step in stepdicts:
        steps.append(step['step'])

    items = list(steps)
    count = len(items)

    for i, key in enumerate(items):
        connector = '└── ' if i == count - 1 else '├── '
        print(prefix + connector + Fore.RED+key+Fore.RESET)

        extension = '    ' if i == count - 1 else '│   '

        COUNTS['steps'] += 1
        print_step(itemdb,thisitem.steps[i], prefix + extension)



def print_item_helper(itemdb, requesteditem):
    global SEEN
    SEEN = []
    global COUNTS
    COUNTS = {'tools': 0, 'raw_materials': 0, 'steps': 0, 'duplicates': 0}

    print(f"Displaying information for: "+Fore.MAGENTA+f"{requesteditem}"+Fore.RESET)
    print_item(itemdb, requesteditem)
    print(f"Counts: {COUNTS}")


def main():
    itemdb = fctcdb.ItemDB(ITEMDBFILE, create_if_needed=False)
    def is_user_requested(item):
        return hasattr(item,'user_requested') and item.user_requested

    user_requested_items = itemdb.filter_items(is_user_requested)

    if len(sys.argv) != 2:
        print(f"Incorrect number of arguments. Usage: {sys.argv[0]} <item>")
        return

    requesteditem = sys.argv[1]

    if requesteditem not in user_requested_items and requesteditem != 'all':
        print(f"Item '{requesteditem}' is not a known, user requested item.")
        return

    # If a specific item is requested, print only that item
    if requesteditem != 'all':
        print_item_helper(itemdb, requesteditem)
        return

    # If 'all' is requested, print all items
    for item in user_requested_items:
        print_item_helper(itemdb, item)


if __name__ == '__main__':
    main()

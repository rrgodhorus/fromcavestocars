'''This is the database for the from caves to cars game.
It contains the requested items, toole/equipment, and raw materials.   Each of 
these is an object with a set of properties.  The database itself is an object 
that contains theste and also has methods to query properties, save / load, 
etc.'''

import json


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)



# JSON serialization helpers...

def is_generic_item_data(data):
    return isinstance(data, dict) and 'typename' in data and data['typename'] == 'GenericItem'

def recursive_deserialize(data):
    if is_generic_item_data(data):
        # Recursively decode all values in the dict before passing to the constructor
        processed = {k: recursive_deserialize(v) for k, v in data.items()}
        return GenericItem(**processed)
    elif isinstance(data, dict):
        return {k: recursive_deserialize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [recursive_deserialize(item) for item in data]
    else:
        return data


class GenericItem:
    '''This is a generic item for the caves to cars game.   This includes
    requested items, tools/equipment, and raw materials.  Each item has a name,
    and a method indicating if it is a base item or a derived item.  A base item
    is an item that is not derived from another item.  A derived item is an
    item that is made inside the game.   All derived items have a steps list
    which contains the steps to make the item.   
    '''

    def __init__(self, name,is_tool=False, **kwargs):
        self.typename = 'GenericItem'
        self.name = name
        self.description = ''
        self.is_tool = is_tool
        self.__dict__.update(kwargs)


    # These two methods are for json serialization.   So is kwargs above
    def to_dict(self):
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, GenericItem):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [item.to_dict() if isinstance(item, GenericItem) else item for item in v]
            elif isinstance(v, dict):
                result[k] = {ik: iv.to_dict() if isinstance(iv, GenericItem) else iv for ik, iv in v.items()}
            else:
                result[k] = v
        return result

    @classmethod
    def from_dict(cls, data):
        return cls(**recursive_deserialize(data))


    def is_base_item(self):
        # I know I could write this more concisely, but I feel this is more
        # readable
        if not self.is_natural:
            return False
        if self.is_part_of_a_larger_item:
            return False
        return True
        

    def __repr__(self):
        # This is a representation of the object which can be used to recreate
        # it.   It writes out the item dictionary as a string.  This is useful 
        # for debugging and for saving/loading the object to/from a file.
        return f'{self.__dict__.items()}'


    def __str__(self):
        return f'{self.name} ({self.description},{self.__dict__})'

    def to_dict(self):
        '''This converts the object to a dictionary.  This is useful for 
        saving/loading the object to/from a file.  The dictionary contains all
        the properties of the object.'''
        return self.__dict__


from os.path import exists

class ItemDB:
    '''This is a database for all items in the from caves to cars game.  
    The database itself is an object that contains the state and also has 
    methods to query all items with certain properties, save / load, etc.'''

    def __init__(self, dbfile=None,create_if_needed=False):
        # I'm going to assume that callers will access this dictionary directly
        self.items = {}
        self.dbfile = dbfile
        if dbfile:
            if exists(dbfile): # from os.path
                self.load()
            elif create_if_needed: 
                self.save() # make it if it is missing and this is requested
            else:
                raise FileNotFoundError(f"Database file {dbfile} does not exist.  Use create_if_needed=True to create it.")

    def filter_items(self, func):
        '''This filters the items in the database using a function and returns
        the item name (not the item itself).  
        The function should take an item object as an argument and return True 
        or False.  This is useful for filtering items based on their 
        properties.'''
        return [k for k, v in self.items.items() if func(v)]


    def save(self):
        '''This saves the database to a file.  The file is a json file.  The 
        filename is the same as the database name.  The file is saved in the 
        current directory.'''
        with open(self.dbfile, 'w') as f:
            json.dump(self.items, f, indent=4, cls=CustomEncoder)

    def load(self):
        '''This loads the database from a file.  The file is a json file.  The 
        filename is the same as the database name.  The file is saved in the 
        current directory.'''
        with open(self.dbfile, 'r') as f:
            loadeddata = json.load(f)
            # I need to do this because this is how I can convert the dicts
            # (which JSON understands) back into objects (which the code 
            # expects)
            self.items = recursive_deserialize(loadeddata)

    def _prevent_infinite_recursion_helper(self, itemname, seen):
        if itemname not in seen:
            seen.append(itemname)

        if not hasattr(self.items[itemname],'steps'):
            # nothing to do...
            return

        for step in self.items[itemname].steps:
            for item in step['tools'][:]: # I copy because I want to modify this
                if item in seen:
                    step['tools'].remove(item)
                else:
                    self._prevent_infinite_recursion_helper(item,seen + [itemname])

            for item in step['raw_materials'][:]: # I copy because I want to modify this
                if item in seen:
                    step['raw_materials'].remove(item)
                else:
                    self._prevent_infinite_recursion_helper(item,seen + [itemname])


    def prevent_infinite_recursion(self):
        '''This prevents infinite recursion when recursing though the items
        by following steps.  In essence, it makes sure than an item does not
        require itself as a tool or raw_material.   If so, it filters out
        that item.   It starts at user requested items'''
        for itemname in self.items:
            if self.items[itemname].user_requested:
                self._prevent_infinite_recursion_helper(itemname,[])

    def _get_item_count_helper(self, itemname):
        '''This returns the tools and materials for this specific item.'''
        tools = []
        raw_materials = []
        if hasattr(self.items[itemname], 'steps'):
            for step in self.items[itemname].steps:
                for item in step['tools']:
                    tools.append(item)
                for item in step['raw_materials']:
                    raw_materials.append(item)

        return tools, raw_materials

    def get_item_count(self, itemname):
        '''This returns the count of items (tools and materials) that are
        required to make the item.   It returns a dict with the unique 
        count for each as well as the total count for each.'''

        retdict = {'uniquetools': 0, 'uniqueraw_materials': 0, 'totaltools': 0, 'totalraw_materials': 0}

        seentools = []
        seenraw_materials = []

        tools, raw_materials = self._get_item_count_helper(itemname)
        while tools or raw_materials:

            if tools:
                item = tools.pop(0)
                retdict['totaltools'] += 1
                if item not in seentools:
                    retdict['uniquetools'] += 1
                    seentools.append(item)
                    newtools, newraw_materials = self._get_item_count_helper(item)
                    tools += newtools
                    raw_materials += newraw_materials
                    # restart the while loop with these items...
                    continue

            if raw_materials:
                item = raw_materials.pop(0)
                retdict['totalraw_materials'] += 1
                if item not in seenraw_materials:
                    retdict['uniqueraw_materials'] += 1
                    seenraw_materials.append(item)
                    newtools, newraw_materials = self._get_item_count_helper(item)
                    tools += newtools
                    raw_materials += newraw_materials
                    # restart the while loop with these items...
                    continue
    
        return retdict


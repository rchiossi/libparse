#!/usr/bin/python

import types

from bindata import BinData
from bytestream import ByteStream

class Entry(object):
    """
    Generic Entry

    This class is used to generate other classes
    dinamically that represents the target file
    format
    """

    "STUB: will be replaced during create() call"
    attr_map = []

    def __init__(self,bstream,offset=None):
        """Generic initialization of an entry structure"""
        self.corrupted = False

        self.attributes = []

        self._prepare_stream(bstream,offset)

        for item in self.attr_map:
            self._add_attr(bstream,item)

    def blob(self):
        """Serialize the bytes of the Entry"""
        blob = bytearray('')

        for attr in self.attributes:
            blob += attr.data

        return blob

    def _prepare_stream(self,bstream,offset):
        """
        Initialize the offset and mode the stream to it.
        The offset should a BinData object to allow references to it
        As so, an update in an offset will update all its the references.
        """
        if offset == None:
            offset = bstream.offset

        if issubclass(offset.__class__,(types.IntType,)):
            self.offset = BinData(4)
            self.offset.init_data_from_int(offset)
        elif issubclass(offset.__class__,(BinData,)):
            self.offset = offset
        elif (issubclass(offset.__class__,(Entry,)) and
              '__int__' in dir(offset)):
            self.offset = offset
        else:
            raise Exception('Invalid type for EntryList offset (%s) in class %s' % 
                            (offset,self))

        bstream.seek(int(self.offset))

    def _get_size(self,bstream,size):
        """
        Return an integer value based on the provided size.
        Size can be an Integer, a BinData object, a method
        in the format func(self,bstream) or an attribute name
        """
        #size is a constant value
        if issubclass(size.__class__,(types.IntType,)):
            return size

        elif issubclass(size.__class__,(BinData,)):
            return int(size)

        #size is calculated from method
        elif (issubclass(size.__class__,(types.FunctionType,)) or
              issubclass(size.__class__,(types.MethodType,))):
            return size(self,bstream)

        elif issubclass(size.__class__,(types.StringType,)):
            #size is in another field from this entry
            if size in self.__dict__.keys():
                return int(self.__dict__[size])
            #size is an evaluated expression
            else:
                return eval(size)
        else:
            raise Exception("Invalid size type in Entry.")

    def _add_attr(self,bstream,attr_item):
        """
        Parse all the structures in the attr_map and
        initialize the attributes in the dictionary
        """
        name = attr_item[0]
        size = self._get_size(bstream,attr_item[1])
        etype = attr_item[2]

        #Raw binary data
        if issubclass(etype,(BinData,)):
            self.attributes.append(etype(size))

            # No need to read if bytestream is already exhausted
            if not bstream.exhausted:
                self.attributes[-1].init_data(bstream.read(size))

        #Entry subclass
        elif issubclass(etype,Entry):
            if size > 0:
                self.attributes.append(etype(bstream))
            else:
                self.__dict__[name] = None
                return

        #Entry List
        elif etype == EntryList:
            if len(attr_item) < 4:
                raise Exception("Missing value for entry %s" % name)
            list_type = attr_item[3]

            self.attributes.append(EntryList(bstream,list_type,size))

        else:
            raise Exception("Invalid type for entry field: %s" % etype)

        #If we could not read, mark self as corrupted
        if bstream.exhausted:
            self.corrupted = True

        #add attr name to dictionary
        self.__dict__[name] = self.attributes[-1]

    @staticmethod
    def create(name,attr_map):
        """
        Creates a specialized Entry

        The attr_list should be a dictionaly with the
        tuple [field_name,field_size,field_mode,extra]

        field_name:
        - String naming the field

        field_size:
        - Integer: Hardcode size in bytes
        - function(bytestrem): A function that will be called on
        target bytestream to get the size
        - String: The name of another field previously read that provides
        the size or an expression to be evaluated with eval()
        that evaluates to an integer

        field_mode:
        - The BinData mode of the field

        extra:
        - for BinData: BinData mode
        - for Entry: unused
        - for EntryList: entry type of the list

        """
        return type(name,(Entry,),{'attr_map':attr_map})

class EntryList(object):
    """
    This class represents a linear list of entry structures
    in the target file. The structures must be sequential in
    the file and must be of the same type.
    """

    def __init__(self,bstream,entry_type,size,offset=None):
        """
        Parse an entry list from a bytestream
        entry_type should be any Entry type generated
        with Entry.create()
        """

        self.data = []
        self.corrupted = False

        self.type = entry_type

        #Set the entry offset
        if offset == None:
            self.offset = BinData(4)
            self.offset.init_data_from_int(bstream.offset)
        elif issubclass(offset.__class__,(types.IntType,)):
            self.offset = BinData(4)
            self.offset.init_data_from_int(offset)
        elif issubclass(offset.__class__,(BinData,)):
            self.offset = offset
        else:
            raise Exception('Invalid type for EntryList offset')

        bstream.seek(int(self.offset))

        if issubclass(size.__class__,(types.IntType,)):
            self.size = BinData(4)
            self.size.init_data_from_int(size)
        elif issubclass(size.__class__,(BinData,)):
            self.size = size
        else:
            raise Exception('Invalid type for EntryList size')


        for i in xrange(int(self.size)):
            self.data.append(self.type(bstream))

            if bstream.exhausted:
                self.corrupted = True
                break

    def blob(self):
        blob = bytearray('')

        for entry in self.data:
            blob += entry.blob()

        return blob

    def __getitem__(self, key):
        if key >= 0 or key < len(self.data):
            return self.data[key]

        return None

    def __setitem__(self, key, value):
        if key >= 0 and key < len(self.data):
            self.data[key] = value

class EntryTable(object):
    """
    Given an EntryList, this class will itarate the list
    and parse 'etype' structures using the 'offset_field'
    attribute of the objects in the EntryList as offset
    for parsing the object.
    """

    def __init__(self,bstream,etype,elist=None,offset_field=None,ignore_offset=None):
        self.corrupted = False

        self.data = []

        self.type = etype
        
        self.parse_list(bstream,elist,offset_field,ignore_offset)

    def parse_list(self,bstream,elist,offset_field,ignore_offset=None):
        """
        Parse entries from an EntryList or and EntryTable
        """

        if elist == None or offset_field == None:        
            return

        for entry in elist.data:
            offset = entry.__dict__[offset_field];
                        
            if ignore_offset != None and int(offset) == ignore_offset:
                continue

            self.parse_entry(bstream,offset)

    def parse_entry(self,bstream,offset):
        self.data.append(self.type(bstream,offset))

        if bstream.exhausted:
            self.corrupted = True

    def __getitem__(self, key):
        for entry in self.data:
            if int(entry.offset) == int(offset):
                return entry

        return None

    def __setitem__(self, key, value):
        for i in xrange(len(self.data)):
            if int(self.data[i].offset) == int(offset):
                self.data[i] = value

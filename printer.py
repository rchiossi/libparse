#!/usr/bin/python

from bindata import BinData

from entry import Entry
from entry import EntryList
from entry import EntryTable

class Printer(object):
    """
    Generic Parseer class

    This class is used to parse the data of Entries of
    a parse object (Entry/EntryList/EntryTable)

    It is intended as a fast way to visualize the data
    being parsed, and speed up the development of a 
    cleaner reading tool.

    """

    def __init__(self):
        self.PAD_INC = 4

    def parse(self,obj,padding=0):
        """
        Generate a string from a parse Object
        """
        data = ''

        if issubclass(obj.__class__,(BinData,)):
            data += self._parse_bindata(obj,padding)
        elif issubclass(obj.__class__,(Entry,)):
            data += self._parse_entry(obj,padding)
        elif issubclass(obj.__class__,(EntryList,)):
            data += self._parse_entry_list(obj,padding)
        elif issubclass(obj.__class__,(EntryTable,)):
            data += '\n' + self._parse_entry_table(obj)
        else:
            raise Exception('Invalid class for Parser: %s' % obj.__class__)

        return data

    def _parse_bindata(self,bindata,padding=0):
        """
        Retrieve the string representatifrom a BinData Object        
        """
        if bindata == None or bindata.size <= 0:
            return 'None'      

        return str(bindata)

    def _parse_entry(self,parse_obj,padding=0):
        """
        Generate a string from an Entry Object
        """
        data = ' '*padding + parse_obj.__class__.__name__ + '{' +'\n'

        padding += self.PAD_INC

        for item in parse_obj.attr_map:
            obj = parse_obj.__dict__[item[0]]

            data += ' '*padding + '{:30s}'.format(item[0]+':')

            if obj == None or issubclass(obj.__class__,(BinData,)):
                data += ' ' + self._parse_bindata(obj) + '\n'
            else:
                data += ' ' + self.parse(obj,padding+self.PAD_INC) + '\n'

        padding -= self.PAD_INC

        data += ' '*padding + '}'

        if parse_obj.corrupted == True:
            data += '\n' + ' '*padding + 'WARNING: Corrupted Data.'

        return data

    def _parse_entry_list(self,obj,padding=0):
        """
        Generate a string from an EntryList Object
        """
        if int(obj.size) == 0:
            return ' '*(padding-self.PAD_INC*2) + 'None'

        data = '\n'

        for i,item in enumerate(obj.data):
            line = self.parse(item,padding)
            tokens = line.split('\n')
            tokens[0] = '%s [%d] {' % (tokens[0][:-1],i)
            data += '\n'.join(tokens) + '\n'

        return data

    def _parse_entry_table(self,obj,padding=0):
        """
        Generate a string from an EntryList Object
        """
        data = ''

        for item in obj.data:
            line = self.parse(item,padding)
            tokens = line.split('\n')
            tokens[0] = '%s [0x%x] {' % (tokens[0][:-1],int(item.offset))
            data += '\n'.join(tokens) + '\n'

        return data

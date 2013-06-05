#!/usr/bin/python

import struct

class BinData:
    """
    Generic Representation of Binary data

    This class should have the following characteristics:
    - It should be easy to manipulate single bytes
    - It should be easy to print the data
    - It should be easy to verify if it is valid
    """
    #Endian Constants
    BIG_ENDIAN = 0x1
    LITTLE_ENDIAN = 0x2

    def __init__(self,size,endian=LITTLE_ENDIAN):
        """
        Initialize a new BinData of given byte size
        e.g.: An uint32 fild should be initialized as BinData(4)
        """
        self.corrupted = False
        self.size = size
        self.endian = endian

        self._fmt = '>I' if endian == self.BIG_ENDIAN else '<I'

        self.data = bytearray(b'\x00'*size)

    def init_data(self,s_data):
        """
        Initialize the actual data.
        Extra bytes will be ignored. If not enough bytes were provided,
        the remaining bytes will be filled with zeroes and the corrupted
        flag will se set to True.
        """
        data = bytearray(s_data)

        if len(data) < self.size:
            stub_size = self.size - len(data)
            self.data = b'\x00'*stub_size + data

            self.corrupted = True
        else:
            self.data = data[:self.size]

    def init_data_from_int(self,i_data):
        """
        Initialize the data from an integer
        this function exists because the BinData is aware
        of the endianess, which allows for generic code
        from the outside.
        """
        self.init_data(struct.pack(self._fmt,i_data))

    def __str__(self):
        """
        Return a String representation of the bytes in data.
        """
        return ''.join(["%02x" % x for x in self.data])

    def __int__(self):
        if len(self.data) < 4:
            if self.endian == self.BIG_ENDIAN:
                conv = bytearray('\x00'*(4 - len(self.data))) + self.data
            else:
                conv = self.data + bytearray('\x00'*(4 - len(self.data)))
        else:
            conv = self.data[:4]

        return struct.unpack(self._fmt,str(conv))[0]


    def __hex__(self):
        return hex(int(self))

    def __hash__(self):
        return hash((self.corrupted, self.size, self.endian, self.data))

    def __eq__(self,other):
        if other == None:
            return False

        return ((self.corrupted, self.size, self.endian, self.data) == 
                (other.corrupted, other.size, other.endian, other.data))

#Utility Classes - Used for the Printer
class BinInt(BinData):
    def __str__(self):
        return str(int(self))

class BinHex(BinData):
    def __str__(self):
        return hex(int(self))

class BinStr(BinData):
    def __str__(self):
        return str(self.data)

#!/usr/bin/python

class ByteStream:
    """
    Provide 'stream like' read interface over a bytearray

    This class will never return any error. If the read
    is not possible, an empty bytearray will be returned
    and the exhausted flag will be set
    """

    def __init__(self,data):
        self.data = bytearray(data)
        self.offset = 0
        self.exhausted = False

    def read(self,size):
        """
        read 'size' bytes from the stream
        """
        if self.offset >= len(self.data):
            self.exhausted = True
            return bytearray('')

        if self.offset + size > self.data:
            self.exhausted = True
            self.offset = len(self.data)
            return self.data[self.offset:]
        else:
            chunk = self.data[self.offset:self.offset+size]
            self.offset += size
            return chunk

    def read_offset(self,size,offset):
        """
        Read 'size' bytes starting from 'offset'
        """
        if offset > len(self.data):
            return bytearray('')

        if len(self.data) < offset+size:
            rsize = len(self.data) - offset
        else:
            rsize = size

        return self.data[offset:offset+rsize]

    def reset(self):
        self.offset = 0
        self.exhausted = False

    def seek(self,offset):
        seek_offset = int(offset) #Avoid type overwrite
        self.offset = seek_offset
        self.exhausted = False

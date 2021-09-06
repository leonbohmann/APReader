import struct
from os import SEEK_CUR
from typing import BinaryIO

ENDIAN_PREFIXES = ("@", "<", ">", "=", "!")


class BinaryReader:
    """
    Base class to read binary files.
    """
    def __init__(self, buf: BinaryIO, endian: str = "@") -> None:
        self.buf = buf
        self.endian = endian

    def align(self) -> None:
        old = self.tell()
        new = (old + 3) & -4
        if new > old:
            self.seek(new - old, SEEK_CUR)

    def read(self, *args) -> bytes:
        return self.buf.read(*args)

    def seek(self, *args) -> int:
        return self.buf.seek(*args)

    def tell(self) -> int:
        return self.buf.tell()

    def read_string(self, size: int = None, encoding: str = "utf-8") -> str:
        if size == 0:
            return ""

        ret = struct.unpack(self.endian + "%is" %
                                (size), self.read(size))[0]

        try:            
            return ret.decode(encoding)
        except:
            try:
                return (b'\xc2' + ret).decode(encoding)
            except:
                return "unknown"

    def read_chars(self, size, encoding: str = "utf-8"):
        ret = b""
        for i in range(size):
            ret += struct.unpack(self.endian + "c", self.read(1))[0]

        return ret.decode(encoding)
    def read_char(self, encoding: str = "ascii"):
        return struct.unpack(self.endian + "c", self.read(1))[0].decode(encoding)
    def read_single(self) -> int:
        return struct.unpack(self.endian + "b", self.read(1))[0]
    
    def read_int16(self) -> int:
        return struct.unpack(self.endian + "h", self.read(2))[0]

    def read_int32(self) -> int:
        return struct.unpack(self.endian + "i", self.read(4))[0]

    def read_double(self) -> float:
        return struct.unpack(self.endian + "d", self.read(8))[0]
    # Aliases
    def read_int(self) -> int:
        return self.read_int32()
"""Extrai um .mas do rFactor 1 (GMOTOR_MAS 2.90, entradas zlib)."""
import struct, zlib, os, sys
def extract(mas, out):
    d = open(mas, 'rb').read(); os.makedirs(out, exist_ok=True)
    n = struct.unpack_from('<I', d, 0x14)[0]; off = 0x1C + n*256
    for i in range(n):
        b = 0x1C + i*256
        name = d[b+4:b+0xF4].split(b'\0')[0].decode('latin1')
        us, cs, _ = struct.unpack_from('<3I', d, b+0xF4)
        blob = d[off:off+cs]; off += cs
        if cs != us: blob = zlib.decompress(blob)
        open(os.path.join(out, name.upper()), 'wb').write(blob)
    return n
if __name__ == '__main__': print(extract(sys.argv[1], sys.argv[2]), 'arquivos')

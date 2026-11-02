"""Leitor minimo de .GMT (rFactor 1): secoes de malha + materiais."""
import struct
SIG = bytes.fromhex('000200ffffffff')  # flags do estagio variam no 1o byte (0x18, 0x98...)
def cstr(b): return b.split(b'\0')[0].decode('latin1')
def parse(path):
    d = open(path, 'rb').read()
    ns, so = struct.unpack_from('<2I', d, 0x174)
    secs = []; last = 0
    for k in range(ns):
        h = struct.unpack_from('<33I', d, so+4+k*0x84)
        flags, offA, offB, nv, ni, offI, mat = h[0], h[1], h[3], h[6], h[8], h[9], h[14]
        secs.append(dict(flags=flags, mat=mat, nv=nv,
                         A=d[offA+4:offA+4+nv*32], B=d[offB+4:offB+4+nv*32],
                         idx=struct.unpack_from('<%dH' % ni, d, offI+4)))
        last = max(last, offI+4+2*ni)
    nm = struct.unpack_from('<I', d, last)[0]
    p = last+4; mats = []
    for m in range(nm):
        name = cstr(d[p:p+64]); mflags = struct.unpack_from('<I', d, p+0x40)[0]
        s0 = d.find(SIG, p+0x40)-0x41
        cnt = struct.unpack_from('<I', d, s0-4)[0]
        stages = [(cstr(d[s0+k*0xac:s0+k*0xac+64]),) + struct.unpack_from('<5I', d, s0+k*0xac+0x48) for k in range(cnt)]
        mats.append(dict(name=name, flags=mflags, stages=stages))
        p = s0+cnt*0xac
    return secs, mats

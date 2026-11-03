"""Cria uma faixa de para-brisa para carros que nao tem o material WCEXTRA1.
A faixa e uma malha nova colada na parte de cima do vidro dianteiro (coordenadas do rFactor: frente = -Z)."""
import numpy as np

def front_glass(tris):
    """Filtra os triangulos do vidro dianteiro (normal para frente e para cima)."""
    n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    n[n[:,1] < 0] *= -1                      # orientacao das faces nao importa
    c = tris.mean(1)
    return tris[(n[:,1] > 0.3) & (n[:,2] < -0.25) & (c[:,2] < 0)]

def _hit(tris, x, z):
    """Altura (y) e normal do vidro no ponto (x, z), ou None."""
    a, b, c = tris[:,0], tris[:,1], tris[:,2]
    v0 = c[:,[0,2]]-a[:,[0,2]]; v1 = b[:,[0,2]]-a[:,[0,2]]; v2 = np.array([x,z])-a[:,[0,2]]
    d00=(v0*v0).sum(1); d01=(v0*v1).sum(1); d11=(v1*v1).sum(1); d02=(v0*v2).sum(1); d12=(v1*v2).sum(1)
    den = d00*d11-d01*d01; ok = np.abs(den) > 1e-12
    u = np.where(ok,(d11*d02-d01*d12)/np.where(ok,den,1),-1); v = np.where(ok,(d00*d12-d01*d02)/np.where(ok,den,1),-1)
    inside = (u >= -1e-6) & (v >= -1e-6) & (u+v <= 1+1e-6)
    if not inside.any(): return None
    y = a[:,1] + u*(c[:,1]-a[:,1]) + v*(b[:,1]-a[:,1])
    i = np.where(inside)[0][np.argmax(y[inside])]
    n = np.cross(b[i]-a[i], c[i]-a[i]); n /= np.linalg.norm(n)
    if n[1] < 0: n = -n
    return y[i], n

def make_strip(glass_tris, depth=0.16, cols=48, rows=6, offset=0.004, margin=0.06):
    """Retorna (pos, uv, idx) da faixa. depth = altura da faixa medida ao longo do vidro (m)."""
    T = front_glass(glass_tris)
    if len(T) == 0: return None
    xs = np.linspace(T[:,:,0].min()+margin, T[:,:,0].max()-margin, cols)
    zgrid = np.linspace(T[:,:,2].min(), T[:,:,2].max(), 200)
    columns = []
    for x in xs:
        hits = [(z,)+h for z in zgrid if (h := _hit(T, x, z)) is not None]
        if len(hits) < 3: continue
        hits = np.array([(z, y) for z, y, _ in hits])
        # anda do topo (z maximo) para baixo ate cobrir 'depth' medido no vidro
        zt = hits[:,0].max(); seg = np.sqrt(np.diff(hits[::-1,0])**2 + np.diff(hits[::-1,1])**2)
        L = np.concatenate([[0], np.cumsum(seg)])
        zs = np.interp(np.linspace(0, min(depth, L[-1]), rows), L, hits[::-1,0])
        col = []
        for z in zs:
            h = _hit(T, x, z) or _hit(T, x, z-2e-3) or _hit(T, x, z+2e-3)
            if h is None: break
            y, n = h; col.append(np.array([x, y, z]) + n*offset)
        if len(col) == rows: columns.append((x, col))
    if len(columns) < 2: return None
    x0, x1 = columns[0][0], columns[-1][0]
    pos, uv = [], []
    for x, col in columns:
        for r, p in enumerate(col):
            pos.append(p); uv.append(((x-x0)/(x1-x0), r/(rows-1)))
    idx = []
    for c in range(len(columns)-1):
        for r in range(rows-1):
            a = c*rows+r; b = a+rows
            idx += [a, b, a+1, a+1, b, b+1]
    return np.array(pos, '<f4'), np.array(uv, '<f4'), np.array(idx, '<u2')

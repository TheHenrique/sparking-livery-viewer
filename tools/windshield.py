"""Cria a faixa de para-brisa para carros que nao tem o material WCEXTRA1.
Recorta a parte de cima do proprio vidro dianteiro (largura toda, do topo ate 'depth' para baixo)
e usa esse pedaco como malha da faixa. Coordenadas do rFactor: frente = -Z."""
import numpy as np

def _normals(T):
    n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    n[n[:,1] < 0] *= -1
    return n

def front_glass(T):
    """Triangulos do para-brisa: parecidos com a normal do centro do vidro e sem passar do topo dele."""
    n = _normals(T); c = T.mean(1)
    cand = (n[:,1] > 0.3) & (n[:,2] < -0.25) & (c[:,2] < 0)
    center = cand & (np.abs(c[:,0]) < 0.2)
    if not center.any(): return T[cand]
    Nc = n[center].mean(0); Nc /= np.linalg.norm(Nc)
    zmax = T[center][:,:,2].max()
    return T[cand & (n @ Nc > np.cos(np.radians(35))) & (c[:,2] < zmax + 0.05)]

def _clip(poly, s, cut):
    """Sutherland-Hodgman: mantem a parte com s >= cut."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i+1) % len(poly)]; sa, sb = s(a), s(b)
        if sa >= cut: out.append(a)
        if (sa >= cut) != (sb >= cut):
            t = (cut - sa) / (sb - sa); out.append(a + t*(b-a))
    return out

def make_strip(glass_tris, depth=0.18, offset=0.004):
    """Retorna (pos, uv, idx, aspecto largura/altura) ou None."""
    T = front_glass(glass_tris)
    if len(T) == 0: return None
    n = _normals(T); area = np.linalg.norm(np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]), axis=1)
    N = (n*area[:,None]).sum(0); N /= np.linalg.norm(N)
    U = np.array([0,1,0]) - N*N[1]; U /= np.linalg.norm(U)       # "para cima" ao longo do vidro
    s = lambda p: float(p @ U)
    smax = max(s(p) for t in T for p in t); cut = smax - depth
    pos, tri_n = [], []
    for t, nn in zip(T, n):
        poly = _clip(list(t), s, cut)
        for k in range(1, len(poly)-1):
            for p in (poly[0], poly[k], poly[k+1]): pos.append(p + nn*offset); tri_n.append(nn)
    if not pos: return None
    pos = np.array(pos); x0, x1 = pos[:,0].min(), pos[:,0].max()
    uv = np.stack([(pos[:,0]-x0)/(x1-x0), (smax - pos @ U)/depth], 1)
    idx = np.arange(len(pos))
    return pos.astype('<f4'), uv.astype('<f4'), idx.astype('<u2'), (x1-x0)/depth

"""Converte um carro do rFactor 1 (pasta com .mas + Graphics.gen) em .glb para o site.
uso: python3 convert_car.py "<pasta do carro>" <saida.glb> [--banner TEXTO] [--front DZ] [--rear DZ] [--no-auto]
- escolhe as malhas do maior LOD lendo o *Graphics.gen (sem piloto, capacete, cockpit, sombra, colisao)
- --banner: troca a faixa do para-brisa (WCEXTRA1) por fundo preto com o TEXTO em branco
- mede o centro dos arcos na carroceria e centraliza as rodas (DZ em metros, + = para tras)"""
import os, sys, re, glob, tempfile, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mas import extract
from gmt import parse
from build import build, corner

EXCLUDE = re.compile(r'(COLLISION|SHADOW|DRIVER|HELMET|COCKPIT|CPIT|BACKFIRE|GLO(_|\.)|GLOW|STEERING|SWHEEL|DIRTSCREEN|_LOD[2-9]|_LOD[B-Z])', re.I)
LOD = re.compile(r'_(EXP|A|B|C|LOD1|LODA)(?=(_|\.GMT$))', re.I)

def pick_meshes(gen, available):
    names = []
    for n in re.findall(r'MESHFILE\s*=\s*([^\s]+)', open(gen, errors='ignore').read(), re.I):
        u = n.upper()
        if u in available and u not in names and not EXCLUDE.search(u): names.append(u)
    # agrupa por nome sem o sufixo de LOD e fica com o mais detalhado (EXP > A > B > C)
    rank = {'EXP':0,'A':1,'LOD1':1,'LODA':1,'B':2,'C':3}
    best = {}
    for u in names:
        m = LOD.search(u)
        key, r = (LOD.sub('', u, count=1), rank[m.group(1).upper()]) if m else (u, 1)
        if key not in best or r < best[key][1]: best[key] = (u, r)
    return [v[0] for v in best.values()]

def verts(path):
    s, _ = parse(path)
    return np.concatenate([np.frombuffer(x['A'], '<f4').reshape(-1,8)[:,:3] for x in s]) if s else np.zeros((0,3))

def arch_offsets(ext, files):
    body = [f for f in files if re.search(r'BODY|BUMPER|HOOD', f) and not corner(f)]
    tyres = {corner(f): f for f in files if corner(f) and re.search(r'TYRE|TIRE', f)}
    if not body or len(tyres) < 4: return None
    B = np.concatenate([verts(os.path.join(ext, f)) for f in body])
    res = {}
    for c, f in tyres.items():
        W = verts(os.path.join(ext, f))
        zc = (W[:,2].min()+W[:,2].max())/2; yc = (W[:,1].min()+W[:,1].max())/2
        xo = np.abs(W[:,0]).max(); sgn = np.sign(W[:,0].mean())
        mids = []
        for dy in (0.0, 0.1, 0.2):
            sel = B[(np.abs(B[:,0]) > xo-0.12) & (np.sign(B[:,0]) == sgn) & (np.abs(B[:,1]-(yc+dy)) < 0.02) & (np.abs(B[:,2]-zc) < 0.8)]
            z = np.sort(sel[:,2])
            if len(z) < 2: continue
            i = np.argmax(np.diff(z)); gap = z[i+1]-z[i]
            if 0.45 < gap < 1.1 and z[i] < zc < z[i+1]: mids.append((z[i]+z[i+1])/2)
        res[c] = (float(np.median(mids)) - zc) if mids else None
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('car'); ap.add_argument('out')
    ap.add_argument('--front', type=float); ap.add_argument('--rear', type=float)
    ap.add_argument('--no-auto', action='store_true')
    ap.add_argument('--banner')
    a = ap.parse_args()
    gen = glob.glob(os.path.join(a.car, '*raphics.gen'))[0]
    masname = [m for m in re.findall(r'MASFILE\s*=\s*([^\s]+)', open(gen, errors='ignore').read(), re.I) if os.path.exists(os.path.join(a.car, m))][0]
    ext = tempfile.mkdtemp(prefix='gmt_')
    extract(os.path.join(a.car, masname), ext)
    files = pick_meshes(gen, set(os.listdir(ext)))
    print('malhas:', ' '.join(files))
    front = a.front or 0.0; rear = a.rear or 0.0
    if not a.no_auto and a.front is None and a.rear is None:
        off = arch_offsets(ext, files)
        print('desvio roda->arco (m):', {k: (round(v,3) if v is not None else None) for k,v in (off or {}).items()})
        if off:
            f = [v for k,v in off.items() if k in ('LF','RF') and v is not None]
            r = [v for k,v in off.items() if k in ('LR','RR') and v is not None]
            if f and abs(np.mean(f)) > 0.03: front = round(float(np.mean(f)), 3)
            if r and abs(np.mean(r)) > 0.03: rear = round(float(np.mean(r)), 3)
    print('ajuste aplicado: dianteiras', front, 'traseiras', rear)
    mats = build(ext, files, a.out, front, rear, banner=a.banner)
    if a.banner and 'WCEXTRA1' not in mats and 'BANNER_GERADO' not in mats: print('aviso: nao foi possivel criar a faixa do para-brisa')
    print('materiais:', ' '.join(mats))
    print('OK', a.out, round(os.path.getsize(a.out)/1e6, 2), 'MB')

if __name__ == '__main__': main()

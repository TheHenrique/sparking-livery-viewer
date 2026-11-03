"""Converte as malhas de um carro (GMT extraidos do .mas) em um unico .glb.
Uso direto: ver convert_car.py, que escolhe as malhas e calcula os ajustes."""
import os, json, struct, io, re
import numpy as np
from PIL import Image
from gmt import parse
from banner import make as make_banner
from windshield import make_strip

SKIP_TEX = ('CUBEMAP', 'EMAP_')
SKIN_MAT = 'WCCARBODY'
BANNER_MAT = 'WCEXTRA1'   # faixa do para-brisa
CORNER = re.compile(r'_(LF|RF|LR|RR)(_|\.|$)')
WHEELISH = re.compile(r'(TYRE|TIRE|WHEEL|RIM|DISC|CALIPER)')

def diffuse(m):
    for st in m['stages']:
        n = st[0].upper()
        if n and n != 'MATH' and not n.startswith(SKIP_TEX) and n.endswith(('.DDS', '.TGA', '.BMP')): return n

def corner(name):
    """'LF'/'RF'/'LR'/'RR' para pecas de roda, senao None."""
    n = name.upper()
    if not WHEELISH.search(n): return None
    m = CORNER.search(n)
    return m.group(1) if m else None

def build(ext, files, out, front_dz=0.0, rear_dz=0.0, banner=None, log=print):
    ext = os.path.join(ext, '')
    bin_ = bytearray(); bviews=[]; accs=[]; meshes=[]; nodes=[]; mats=[]; matidx={}; images=[]; texs=[]; imgidx={}
    def addview(b, target=None):
        while len(bin_) % 4: bin_.append(0)
        bv = {'buffer':0,'byteOffset':len(bin_),'byteLength':len(b)}
        if target: bv['target'] = target
        bin_.extend(b); bviews.append(bv); return len(bviews)-1
    def addacc(arr, typ, comp, target, mm=False):
        a = {'bufferView':addview(arr.tobytes(),target),'componentType':comp,'count':int(arr.shape[0]),'type':typ}
        if mm: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        accs.append(a); return len(accs)-1
    def image(name, transform=None):
        cache = name if transform is None else name + '#banner'
        if cache in imgidx: return imgidx[cache]
        p = ext+name
        if not os.path.exists(p): imgidx[cache] = None; log('  textura fora do .mas:', name); return None
        im = Image.open(p); im.load(); im = im.convert('RGBA')
        if transform: im = transform(im).convert('RGBA')
        buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
        images.append({'bufferView':addview(buf.getvalue()),'mimeType':'image/png','name':name})
        texs.append({'source':len(images)-1,'sampler':0})
        imgidx[cache] = (len(texs)-1, im.size, im.getextrema()[3][0] < 128); return imgidx[cache]
    glass = []
    for f in files:
        secs, ms = parse(ext+f); prims = []
        c = corner(f); dz = (front_dz if c in ('LF','RF') else rear_dz) if c else 0.0
        for s in secs:
            m = ms[s['mat']]; key = m['name'] or os.path.splitext(f)[0]
            if key not in matidx:
                tex = diffuse(m); blend = bool(m['flags'] & 0x20)
                mat = {'name':key,'pbrMetallicRoughness':{'metallicFactor':0.0,'roughnessFactor':0.5}}
                if key == SKIN_MAT: tex = None      # skin padrao fora: o site aplica a skin enviada
                if key == BANNER_MAT and banner and tex:
                    def _banner(im):   # mantem o alfa original (formato da faixa)
                        new = make_banner(im.convert('RGB'), banner).convert('RGBA'); new.putalpha(im.getchannel('A')); return new
                    info = image(tex, _banner)
                else:
                    info = image(tex) if tex else None
                if key == SKIN_MAT: mat['pbrMetallicRoughness']['baseColorFactor'] = [0.02,0.02,0.02,1]
                if info: mat['pbrMetallicRoughness']['baseColorTexture'] = {'index':info[0]}
                elif re.search(r'TIRE|TYRE', key.upper()): mat['pbrMetallicRoughness']['baseColorFactor'] = [0.06,0.06,0.06,1]
                elif re.search(r'RIM|WHEEL|DISC', key.upper()): mat['pbrMetallicRoughness']['baseColorFactor'] = [0.25,0.25,0.25,1]
                if blend: mat['alphaMode'] = 'BLEND'; mat['doubleSided'] = True
                elif info and info[2] and 'DECAL' in (key + (tex or '')).upper():
                    mat['alphaMode'] = 'MASK'; mat['alphaCutoff'] = 0.5   # decal sem flag, recorta pelo alfa
                mats.append(mat); matidx[key] = len(mats)-1
            if not s['idx']: continue
            A = np.frombuffer(s['A'], '<f4').reshape(-1,8); B = np.frombuffer(s['B'], '<f4').reshape(-1,8)
            if 'BODY' in f.upper() and re.search(r'WINDOW|GLASS', key.upper()) and (m['flags'] & 0x20):
                glass.append(A[:,:3][np.array(s['idx']).reshape(-1,3)].astype(float))
            pos = A[:,0:3].copy(); nrm = A[:,3:6].copy(); uv = B[:,0:2].copy()
            uv[:,1] += np.where(uv[:,1] < 0, 1.0, 0.0)
            pos[:,2] += dz
            pos[:,0] *= -1; nrm[:,0] *= -1        # rFactor e mao-esquerda: espelha X (ja corrige o sentido das faces)
            l = np.linalg.norm(nrm, axis=1, keepdims=True); l[l == 0] = 1; nrm = (nrm/l).astype('<f4')
            idx = np.array(s['idx'], '<u2')
            prims.append({'attributes':{'POSITION':addacc(pos.astype('<f4'),'VEC3',5126,34962,True),
                          'NORMAL':addacc(nrm,'VEC3',5126,34962),'TEXCOORD_0':addacc(uv.astype('<f4'),'VEC2',5126,34962)},
                          'indices':addacc(idx,'SCALAR',5123,34963),'material':matidx[key]})
        if prims:
            meshes.append({'name':os.path.splitext(f)[0],'primitives':prims}); nodes.append({'name':meshes[-1]['name'],'mesh':len(meshes)-1})
    if banner and BANNER_MAT not in matidx and glass:
        strip = make_strip(np.concatenate(glass))
        if strip:
            pos, uv, idx, aspect = strip
            im = make_banner(Image.new('RGB', (1024, max(64, int(round(1024/aspect))))), banner).convert('RGBA')
            buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
            images.append({'bufferView':addview(buf.getvalue()),'mimeType':'image/png','name':'banner_gerado.png'})
            texs.append({'source':len(images)-1,'sampler':0})
            mats.append({'name':'BANNER_GERADO','doubleSided':True,'pbrMetallicRoughness':{'metallicFactor':0.0,'roughnessFactor':0.9,'baseColorTexture':{'index':len(texs)-1}}})
            pos = pos.copy(); pos[:,0] *= -1
            nrm = np.tile(np.array([0,1,0],'<f4'), (len(pos),1))
            prim = {'attributes':{'POSITION':addacc(pos,'VEC3',5126,34962,True),'NORMAL':addacc(nrm,'VEC3',5126,34962),'TEXCOORD_0':addacc(uv,'VEC2',5126,34962)},
                    'indices':addacc(idx,'SCALAR',5123,34963),'material':len(mats)-1}
            meshes.append({'name':'BANNER_GERADO','primitives':[prim]}); nodes.append({'name':'BANNER_GERADO','mesh':len(meshes)-1})
            log('  faixa de para-brisa gerada sobre o vidro')
    gl = {'asset':{'version':'2.0','generator':'sparking-livery-viewer gmt2glb'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],
          'nodes':nodes,'meshes':meshes,'materials':mats,'accessors':accs,'bufferViews':bviews,'buffers':[{'byteLength':len(bin_)}],
          'images':images,'textures':texs,'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]}
    j = json.dumps(gl, separators=(',',':')).encode()
    while len(j) % 4: j += b' '
    while len(bin_) % 4: bin_.append(0)
    open(out,'wb').write(struct.pack('<III',0x46546C67,2,28+len(j)+len(bin_))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(bin_),0x004E4942)+bin_)
    return [m['name'] for m in mats]

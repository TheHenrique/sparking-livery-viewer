# Sparking GT3 · Livery Viewer

Site estático para visualizar skins (PNG, qualquer resolução) nos carros GT3 do mod Sparking GT3 do rFactor 1, em 3D, no navegador.

- `index.html`, `style.css`, `src/main.js` — o site (Three.js via CDN, sem build).
- `cars.json` — lista de carros; `skinMaterial` é o material do .gmt que recebe a skin.
- `models/` — modelos convertidos (.glb).
- `tools/` — conversão do jogo para .glb (Python + numpy + Pillow):
  ```
  python3 tools/convert_car.py "<pasta do carro>" models/<id>.glb
  ```
  Lê o `*Graphics.gen`, pega as malhas do maior LOD (sem piloto, capacete e cockpit) e centraliza as rodas nos arcos automaticamente
  (ajuste manual: `--front` / `--rear` em metros, + = para trás).

Rodar localmente: `python -m http.server` na raiz e abrir http://localhost:8000.
Deploy: importar o repositório na Vercel (Framework preset: Other, sem build).

A carroceria (material `WCCARBODY`) sai preta, sem a skin padrão do mod; o site aplica a skin enviada.

Observações por carro:
- BMW M4 GT3: rodas centralizadas automaticamente (dianteiras 0,136 m e traseiras 0,083 m para trás).
- Nissan GT-R Nismo GT3: aro, pneu e disco usam texturas que não estão no .mas do carro; ficam em cinza/preto.

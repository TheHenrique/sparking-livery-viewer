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
  Faixa do para-brisa com o nome da montadora (fundo preto, texto branco): `--banner "PORSCHE"`.
  Carros sem faixa própria (WCEXTRA1) ganham uma faixa gerada sobre o topo do vidro (ex.: Corvette). O Aston Martin já tem a faixa no vidro e foi mantido.
  Fonte: Poppins Bold (`tools/fonts`, licença SIL Open Font License).

Rodar localmente: `python -m http.server` na raiz e abrir http://localhost:8000.
Deploy: importar o repositório na Vercel (Framework preset: Other, sem build).

A carroceria (material `WCCARBODY`) sai preta, sem a skin padrão do mod; o site aplica a skin enviada.

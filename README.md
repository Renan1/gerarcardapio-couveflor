# Gerador de Cardápio — Couve Flor

Ferramenta interna que desenha a imagem diária do cardápio (1080×1920) no padrão visual do restaurante.
Roda 100% no navegador, sem backend.

- **Uso:** abra o site, escolha o dia, selecione/cole os pratos, toque em *Gerar cardápio* e depois em *Salvar na Galeria*.
- **Desenvolvimento:** leia o [`CLAUDE.md`](CLAUDE.md). Servidor local: `python -m http.server 8000`.
- **Novos ícones:** `python tools/extract_icons.py tools/sheets/<folha>.json --out /tmp/teste --debug`.

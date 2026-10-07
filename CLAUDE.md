# CLAUDE.md — Gerador de Cardápio · Couve Flor

> Leia este arquivo inteiro antes de mexer em qualquer coisa. Ele registra decisões, parâmetros que
> funcionaram e bugs reais que já aconteceram neste projeto. Idioma do produto e dos commits: **pt-BR**.

## 1. O que é

Ferramenta web de **uso interno** do restaurante Couve Flor (Couve Flor LTDA). O operador cola/seleciona os
pratos do dia, escolhe o dia da semana e o sistema **desenha a imagem do cardápio (9:16, 1080×1920)** no
mesmo padrão visual que antes era gerado manualmente numa IA (Adapta). A imagem é salva na galeria do
celular e enviada por WhatsApp.

- **Sem backend, sem API paga, sem build step.** Tudo roda no navegador (Canvas 2D). Isso é decisão
  deliberada: o fluxo com IA generativa foi descartado por custo e por variar o visual a cada geração.
- Uso real: ~2 vezes por dia, por 1 operador, em **Chrome/Android** e **Safari/iPhone** (também desktop).
- Repositório: `gerarcardapio-couveflor` (GitHub, público). Deploy: GitHub Pages + subdomínio via CNAME no Cloudflare.

## 2. Estado atual do código (importante)

- `index.html` na raiz é um **monólito de ~6 MB**: HTML + CSS + JS + **todos os ícones embutidos em base64**
  (`ICONS_B64`, `KEYWORD_MAP`, `ICON_GALLERY`). Funciona e está em produção. **Não quebre isso** sem ter a
  versão nova testada.
- O monólito foi gerado por scripts avulsos; os arquivos-fonte originais **não existiam** em disco.
  Por isso este repositório já traz tudo **extraído** do monólito:
  - `assets/icons/*.png` — 147 ícones (PNG com fundo transparente)
  - `assets/brand/` — logo, rodapé, favicons, ícones de app
  - `data/keyword_map.json`, `data/icon_gallery.json`
  - `manifest.webmanifest` — com caminhos de arquivo (no monólito ele vai embutido como data URI)
- **Tarefa nº 1 sugerida (refatoração):** quebrar o monólito em `index.html` + `css/style.css` + `js/app.js`
  carregando ícones por URL (`assets/icons/<slug>.png`) com *lazy load*, sem framework e sem bundler.
  Critérios de aceite na seção 12.

## 3. Estrutura do repositório

```
CLAUDE.md                 este arquivo
index.html                monólito atual (produção)
manifest.webmanifest      manifesto PWA (versão com arquivos)
assets/
  icons/<slug>.png        147 ícones de pratos
  brand/                  logo.png, footer.png, favicon-16/32.png, apple-touch-icon.png, icon-192/512.png
data/
  keyword_map.json        [[texto, slug], ...] — 164 entradas (nomes + apelidos), ordenadas por tamanho desc
  icon_gallery.json       [{name, slug, category}, ...] — 147 entradas, na ordem de exibição
tools/
  extract_icons.py        extrai ícones de uma folha-grade (ver seção 8)
  sheets/*.json           configuração (calibração) de cada folha
  requirements.txt        pillow, numpy, scipy
reference/
  sheets-grade/*.png      as 6 folhas-grade geradas na Adapta (fonte dos ícones novos)
  listas-antigas/IMG_*.png cardápios antigos em formato lista (fonte dos ~57 ícones originais)
  gabarito-visual-original.jpeg   o cardápio "como era feito antes" — é a referência de fidelidade visual
```

## 4. Como rodar localmente

```bash
python -m http.server 8000     # e abra http://localhost:8000
```

**Não abra por `file://` depois da refatoração.** Com os ícones como PNGs separados, o Chrome trata cada `file://` como
origem única, o canvas fica *tainted* e `toDataURL()` lança `SecurityError`. Além disso `navigator.share`/`canShare`
exigem **contexto seguro (HTTPS ou localhost)** — foi a causa provável do botão de compartilhar falhar no Android
com o arquivo aberto localmente. No monólito atual o taint não ocorre (tudo é data URI), mas o share continua
dependendo de HTTPS. Em produção é HTTPS (GitHub Pages), então não há problema.

## 5. Deploy

1. GitHub Pages: *Settings → Pages → Deploy from a branch → `main` / `(root)`*.
2. Domínio próprio: campo *Custom domain* no Pages (cria o arquivo `CNAME` na raiz — **não apague**).
3. Cloudflare DNS: registro `CNAME` do subdomínio → `<usuario>.github.io`. Comece com nuvem **cinza** (DNS only).
   Se ativar o proxy (laranja), o SSL/TLS do Cloudflare tem que estar em **Full**, nunca **Flexible**
   (senão há loop de redirecionamento com o *Enforce HTTPS* do GitHub).
4. Marcar *Enforce HTTPS* quando o *DNS check* ficar verde.

Motivo da escolha: o Netlify gratuito limitava por créditos; para ~2 acessos/dia, Pages é mais que suficiente.
Cloudflare Pages seria a alternativa (banda ilimitada), mas o dono já domina GitHub Pages + CNAME.

## 6. Especificação do render (não mude sem comparar com o gabarito)

Canvas **1080×1920**. Tudo desenhado em `render()`.

| Elemento | Valor |
|---|---|
| Fundo | `#F9F6EC` |
| Borda externa | retângulo arredondado `(40,40,W-80,H-80)`, raio 44, 6px, `#3A4620` |
| Borda interna | `(50,50,W-100,H-100)`, raio 38, 2px, `rgba(90,100,70,.6)` |
| Logo | `assets/brand/logo.png`, largura 620, centralizada, `y=60` |
| Título | `Cardápio do Dia - {dia}`, **Poppins bold 54px**, `#3A4620`, centralizado, baseline `y = logoY+logoH+50` |
| Início da lista | `startY = logoY+logoH+100`; limite inferior `H-150` |
| Altura da linha | `rowH = min(112, (H-150-startY)/n)` |
| Bolinha | raio 10, `#5C6B33`, `x=160` |
| Slot do ícone | centro `x=160+112`, `boxW=156`, `boxH=min(102, rowH*0.88)`; ícone em *contain* (nunca corta) |
| Texto do item | **Poppins bold 42px**, `#1E1E1E`, `x=160+212`, `textBaseline=middle` |
| Rodapé | `assets/brand/footer.png`, largura 230, `y=H-140` |

Fontes: Poppins via Google Fonts (`wght@600;700`). **A fonte é opcional**: nunca bloqueie a UI esperando-a
(ver seção 10, bug nº 3).

Paleta: `--olive #5C6B33`, `--olive-dark #3A4620`, `--ink #1E1E1E`, `--cream #F7F3E9`.

## 7. Biblioteca de ícones e casamento item → ícone

- Cada ícone é um PNG transparente, **recortado rente ao desenho** (+4–6px de margem), arquivo
  `assets/icons/<slug>.png`.
- **Slug** = nome sem acento, minúsculo, qualquer não-alfanumérico vira `_` (função `slugify` em
  `tools/extract_icons.py`). Ex.: "Filé de frango a pizzaiolo" → `file_de_frango_a_pizzaiolo`.
- **Categorias** (ordem de exibição na galeria): `Proteínas` → `Grãos, Massas e Feijões` →
  `Guarnições e Vegetais` → `Saladas e Frutas`; dentro de cada uma, ordem alfabética (sem acento).
- **Casamento:** o texto digitado é normalizado (minúsculo, sem acento, trim) e percorre `keyword_map.json`
  **do maior para o menor termo**; vale o primeiro cujo termo normalizado esteja **contido** no texto. Assim
  "bolinho de arroz" ganha de "arroz". Sem correspondência → tigela genérica desenhada em canvas e o item
  aparece em "Sem ícone específico…".
- `keyword_map.json` tem os nomes oficiais **e apelidos genéricos** (ex.: "abobora"→moranga, "frango"→isca_de_frango_grelhado,
  "peixe"→peixe, "lombo"/"bife"→bife_de_lombo). Apelidos antigos podem apontar para um ícone **provisório** que hoje
  já tem ícone próprio — veja a seção 11.
- Ao adicionar um prato: PNG em `assets/icons/`, entrada em `icon_gallery.json` (com categoria) e em
  `keyword_map.json`, e **reordenar** `keyword_map.json` por tamanho decrescente.

## 8. Pipeline para criar ícones novos (parâmetros que funcionaram)

Fluxo do dono: gera na Adapta uma **folha-grade** (4–6 colunas, ícone + legenda abaixo, 864×1536, mesmo cartão
da marca), salva em `reference/sheets-grade/` e roda o extrator.

```bash
pip install -r tools/requirements.txt
# 1) copie um JSON de tools/sheets/ e calibre (abaixo)
# 2) teste sem sobrescrever e confira o contact sheet escuro:
python tools/extract_icons.py tools/sheets/minha_folha.json --out /tmp/teste --debug
# 3) se estiver OK, rode sem --out (grava em assets/icons/)
```

**Calibração de uma folha nova** — desenhe linhas horizontais a cada 20px sobre a imagem e leia o **centro**
da 1ª e da última linha de ícones: `row_h = (centro_última − centro_primeira)/(n_linhas−1)` e
`grid_top = centro_primeira − row_h/2`. Meça `x0`/`x1` = primeiro/último pixel **branco puro**
(>250 nos 3 canais) numa linha sem conteúdo. **`x0/x1` variam entre folhas** (87–775 numa, 43–821 noutra).

**Regras que custaram caro (não repita):**
1. **Linhas incompletas se redistribuem na largura toda.** Uma linha com 4 itens numa grade de 5 não usa as
   colunas da grade de 5 — cada linha é espaçada por `largura/itens_da_linha`. (O script já faz isso.)
2. **Nunca recorte por caixa fixa "adivinhada".** A 1ª extração cortou a borda de dezenas de pratos. O método
   certo é janela generosa + maior componente conexo (máscara: `saturação>0.08 OU valor<0.35`, dilatação 4,
   margem 6). Potes com alça precisam dessa folga horizontal.
3. **Branco → transparente** com limiar `soma(RGB) > 245*3`. Efeito colateral aceito: grãos brancos (arroz) ficam
   "furados" — só parecem certos sobre fundo claro. **Nunca teste ícones só sobre fundo branco**: use fundo
   escuro (`--debug` já faz) para enxergar corte e transparência.
4. Auditar **em zoom** e com fundo escuro. Miniaturas pequenas escondem corte e escondem falsos alarmes.
5. Cuidado ao extrair de imagens em **formato lista** (`reference/listas-antigas`): a linha vizinha invade a
   janela e o maior componente pode ser o ícone errado (aconteceu com "Repolho", que saiu como Alface).

## 9. Funcionalidades já implementadas

- **Gerar** (canvas) e **Salvar na Galeria**: `navigator.share({files})` quando disponível (abre a folha nativa:
  "Salvar imagem"/"Adicionar a Fotos"); senão `<a download>`. Nenhum site salva direto na galeria sem confirmação.
- **Galeria "Veja as opções disponíveis"**: grade agrupada por categoria, com busca; toque no prato adiciona
  o nome (canônico) à lista; evita duplicata.
- **Limpar**: esvazia a caixa de itens.
- **Histórico** (`localStorage`, chave `couveflor_menu_history`): cada "Gerar" grava `{ts, day, items}`
  (ignora se idêntico ao último). Lista "mais recente primeiro", **Usar este cardápio**, **Excluir**,
  **Apagar histórico**, **Exportar CSV** (formato longo, UTF-8 com BOM, colunas
  `Data,Hora,Dia da semana,Item` — uma linha por prato).
  Limitação: o histórico vive **só naquele navegador/aparelho** (não sincroniza; some se limpar dados).
- **Mobile/PWA:** `apple-touch-icon`, metas `apple-mobile-web-app-*`/`mobile-web-app-capable`,
  `theme-color #5C6B33`, manifesto com ícones 192/512.
- **Aviso de itens sem ícone** abaixo da imagem.

## 10. Bugs reais já ocorridos (lições)

1. **Pacote de dados desatualizado:** o HTML foi reconstruído com um `icons_b64.json` antigo, anterior ao fundo
   transparente → retângulos brancos cortando as bolinhas. *Lição:* sempre gerar o bundle a partir da pasta de
   ícones atual e validar `ICON_GALLERY ⊆ ICONS_B64`.
2. **Constante que não entrou no HTML:** `ICON_GALLERY` foi anexada ao arquivo de dados depois de o HTML já
   ter sido montado → `ReferenceError` ao clicar na galeria. *Lição:* reconstruir o HTML inteiro, nunca
   remendar um HTML já montado.
3. **Travamento no Android com rede ruim:** os botões só eram liberados depois de carregar a fonte do Google;
   com conexão ruim ficava "Carregando…" para sempre. *Correção:* `withTimeout` (fontes 2,5s, ícones 4s) e
   *fail-safe* de 6s (`finishInit`). **Nunca condicione a UI a recurso externo.**
4. **Só o favicon na tela inicial do Android:** faltava Web App Manifest (o iOS usa `apple-touch-icon`, por isso
   funcionava). Com HTTPS + `manifest.webmanifest` real, o Chrome oferece instalação de verdade.
5. **Cache de versão antiga** no Chrome/Android ao reabrir arquivo local com o mesmo nome — se algo "sumir",
   suspeite de cópia em cache antes de depurar o código.
6. Todos os `<button>` devem ter `type="button"` explícito.

## 11. Problemas conhecidos / dívida técnica (pendências reais)

- **Texto longo estoura o cartão.** Com Poppins bold 42px há ~658px úteis; "Couve flor com cenoura e chuchu"
  mede ~724px e passa da borda. Falta reduzir a fonte (ou quebrar linha) por item.
- **Muitos itens:** a fonte é fixa em 42px; acima de ~22 itens as linhas ficam apertadas/sobrepostas
  (`rowH` encolhe, a fonte não). Escalar fonte e ícone com `rowH`.
- **Ícone `fruta` errado:** mostra uma tigela de beterraba. Deveria ser banana+maçã+laranja (veja
  `reference/listas-antigas/IMG_1187.png`, última linha). Reextrair.
- **Ícone `pure`** (legado) traz um pedaço da tigela vizinha no topo — duplicado de `pure_de_batata`;
  consolidar. **`isca_de_frango_empanada`** parece carne enrolada, não tiras empanadas — conferir.
- **Os ~57 ícones da 1ª leva (lista)** foram extraídos antes do método robusto; só alguns foram refeitos.
  Auditar todos em fundo escuro; a maioria foi coberta de novo pelas folhas-grade, mas confira os que sobraram.
- **Casamento por substring** pode errar. Melhorar com limite de palavra/correspondência aproximada e prioridade ao
  nome canônico. **Apelidos obsoletos para revisar** em `keyword_map.json`: `linguica`→churrasco_misto (já existem
  `linguica_toscana` e `linguica_assada`), `ovo`→virado (dúbio), `tomate` e `brocolis` apontam para ícones só parecidos,
  `costela`→carne_assada (já existe `costelinha`). Itens que só casam por apelido não têm ícone próprio.
- **Sem domingo** no seletor de dia (só segunda a sábado). Confirmar com o dono se domingo deve entrar.
- **Monólito de 6 MB:** carrega e decodifica 149 imagens no início; em Android fraco pesa. Resolver na refatoração.
- Sem testes automatizados; só validação manual e `node --check`.

## 12. Roadmap sugerido (nessa ordem)

1. **Refatorar sem mudar comportamento** (`index.html` + `css/` + `js/` + ícones por URL, lazy load).
   *Aceite:* a imagem gerada fica **idêntica** (diff de pixels) à do monólito para 3 cardápios de teste
   (ex.: Quarta de 12 itens, Sexta de 15 itens, um com item sem ícone); abre em < 1s no Android;
   nenhum `localStorage` perdido (mantenha a chave `couveflor_menu_history`).
2. Corrigir overflow de texto e escala com muitos itens (seção 11).
3. Corrigir ícones `fruta`, `pure`, `isca_de_frango_empanada`.
4. Service Worker (cache offline dos PNGs) + manifesto real; botão de instalar.
5. Modelos por dia da semana ("segunda padrão") e aviso de item duplicado.
6. Backup/importação do histórico (JSON) para trocar de aparelho.
7. Testes: Playwright (screenshot do canvas) + script que valida integridade
   (`keyword_map ⊆ icons`, `icon_gallery` sem duplicata, todo PNG com alfa).

## 13. Convenções

- Vanilla JS/HTML/CSS. **Sem framework, sem bundler, sem dependência de runtime** — a ferramenta tem 1 operador e
  2 usos/dia; complexidade a mais custa mais do que entrega.
- Nenhum segredo/chave no repositório (é público). Nenhum dado de cliente.
- Commits em pt-BR, no imperativo curto ("Corrige estouro de texto longo").
- Toda mudança visual: compare com `reference/gabarito-visual-original.jpeg` e com o render anterior.
- Antes de commitar mudança em ícones: rodar a validação de integridade (item 7 do roadmap) ou, no mínimo,
  abrir o contact sheet em fundo escuro.

## 14. Nunca faça

- Não troque a abordagem para IA generativa em tempo de execução (custo + inconsistência visual).
- Não use caixa de recorte fixa para ícones (seção 8).
- Não condicione botões a fonte/rede (seção 10, bug 3).
- Não apague `CNAME` nem `manifest.webmanifest`.
- Não reduza o slot do ícone nem use *cover* — o ícone deve caber inteiro (*contain*).

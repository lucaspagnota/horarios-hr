# Horários HR

App das aulas de música do Lucas: grade da semana, fichas dos alunos (música atual, escalas, nível, observações, diário de aulas), repertório de cada instrumento na ordem em que ele ensina, programa do recital de julho e outubro, e reposições.

- **Site:** https://lucaspagnota.github.io/horarios-hr/ (abre no computador e no celular; no Android dá para instalar pelo menu do navegador)
- **APK para Android:** https://github.com/lucaspagnota/horarios-hr/releases/download/apk/HorariosHR.apk

## Como funciona

| Pasta / arquivo | O que é |
|---|---|
| `app/horarios-hr.html` | O app inteiro (HTML, CSS e JavaScript num arquivo só). É o mesmo arquivo publicado dentro do Claude. |
| `scripts/build.py` | Monta o site em `www/`: cabeçalho, ícones, manifest, service worker e as configurações do Firebase. |
| `web/` | Manifest do app instalável, service worker e ícones. |
| `assets/` | Ícone e tela de abertura usados no APK. |
| `firebase/firestore.rules` | Regras do banco: só a conta do Lucas lê e grava. |
| `google.config.json` | ID do cliente OAuth do Google (público) que deixa o app ler os nomes dos arquivos no Google Drive. |
| `.github/workflows/` | `site.yml` monta o site e publica na branch `gh-pages` (GitHub Pages); `apk.yml` gera o APK e atualiza a versão "apk". |

A cada `push` na `main`, o GitHub publica o site e gera um APK novo.

## Dados

- Com o arquivo `firebase.config.json` na raiz, o app pede login (e-mail e senha do Firebase Authentication) e guarda tudo no Cloud Firestore, sincronizado entre computador e celular.
- Sem ele, o app guarda os dados só no aparelho.
- Em **Ajustes** dá para exportar e importar um backup `.json` e baixar a planilha `.xlsx`.
- Nenhum dado de aluno fica neste repositório.

## Repertório

As sequências saem da pasta HR-LUCAS do computador, que o Google Drive para computador sincroniza. Em **Repertório > Atualizar do Drive** (no site), o app entra no Google com permissão só de ver os nomes dos arquivos (`drive.metadata.readonly`), percorre a pasta e grava o catálogo no Firestore. O celular e o APK leem esse catálogo, e **Abrir** mostra o arquivo no visualizador do Drive (Word e PDF).

- O número no começo do nome é a ordem de ensino (`3-O Mar Serenou.docx`, `(MUSICA 1) Marcha.pdf`, `13.1 Monte Castelo.pdf`); arquivos sem número entram como "fora da sequência".
- Cada pasta de instrumento vira um item, e cada subpasta uma seção. A pasta CIFRAS é uma biblioteca de busca, sem ordem.
- O conteúdo das cifras nunca passa pelo app nem por este repositório.

Configuração única no [Google Cloud](https://console.cloud.google.com/) (projeto `horarios-hr`): ativar a **Google Drive API**; criar a tela de consentimento OAuth (Externo, em teste, com a conta do Lucas como usuário de teste); criar um cliente OAuth **Aplicativo da Web** com a origem `https://lucaspagnota.github.io`; colocar o ID em `google.config.json` (`{"clientId": "..."}`).

## Rodar no computador

```bash
npm install
python3 scripts/build.py
cd www && python3 -m http.server 8000
```

## Logo e ícones

A logo fica só em `app/horarios-hr.html` (a constante `LOGO` e as cores `--brand-*`). Para gerar de novo os ícones do site e do APK a partir dela:

```bash
npx playwright install chromium   # só na primeira vez
npm run icons
```

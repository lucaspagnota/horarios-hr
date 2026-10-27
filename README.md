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
| `firebase/storage.rules` | Regras dos arquivos do repertório (Firebase Storage): só a conta do Lucas. |
| `scripts/repertorio.py` | Lê a pasta HR-LUCAS do computador, converte Word para PDF e gera a lista do repertório. |
| `.github/workflows/` | `site.yml` monta o site e publica na branch `gh-pages` (GitHub Pages); `apk.yml` gera o APK e atualiza a versão "apk". |

A cada `push` na `main`, o GitHub publica o site e gera um APK novo.

## Dados

- Com o arquivo `firebase.config.json` na raiz, o app pede login (e-mail e senha do Firebase Authentication) e guarda tudo no Cloud Firestore, sincronizado entre computador e celular.
- Sem ele, o app guarda os dados só no aparelho.
- Em **Ajustes** dá para exportar e importar um backup `.json` e baixar a planilha `.xlsx`.
- Nenhum dado de aluno fica neste repositório.

## Repertório

As sequências saem das pastas do computador (HR-LUCAS). O número no começo do nome do arquivo é a ordem em que a música é ensinada (`3-O Mar Serenou.docx`, `(MUSICA 1) Marcha.pdf`); arquivos sem número entram como "fora da sequência". A pasta CIFRAS vira uma biblioteca de busca, sem ordem.

1. `python3 scripts/repertorio.py "<caminho da pasta HR-LUCAS>"` converte os Word para PDF em `APP HORARIOS AULAS/Repertório/PDFs` (os originais não mudam) e grava `APP HORARIOS AULAS/Repertório/repertorio.json`. Precisa do LibreOffice.
2. No app, no computador: **Ajustes > Repertório > Enviar pasta HR-LUCAS**. O app manda para o Firebase Storage só os arquivos que ainda não estão lá e salva as sequências no Firestore.

Os arquivos nunca vão para este repositório (ele é público).

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

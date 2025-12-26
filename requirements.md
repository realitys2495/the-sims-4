# The Sims 4 Downloader - Requirements

## Original Problem Statement
Criar um programa para PC que baixe o The Sims 4 da nuvem (Google Drive) para o PC do usuário.

## User Requirements
- **Source**: Google Drive (link pré-configurado no sistema)
- **Link configurado**: https://drive.google.com/drive/folders/1CQVPFH5iGWJKcMRFf7ZKSjgPSxFw4ywF
- **File Size**: 76 GB
- **Features**:
  - Barra de progresso do download
  - Verificação de integridade dos arquivos (SHA-256)
  - Extração automática do ZIP
  - Sistema de pause/resume
  - Escolha da pasta de destino (sugestão padrão)
- **Design**: Tema inspirado no The Sims 4

## Architecture Completed

### Backend (FastAPI + MongoDB + Google Drive API)
- **Google Drive Integration**: Pasta configurada: `1CQVPFH5iGWJKcMRFf7ZKSjgPSxFw4ywF`
- `GET /api/folder-info` - Lista arquivos na pasta do Google Drive
- `POST /api/downloads` - Cria novo download da pasta configurada
- `GET /api/downloads/{id}` - Retorna status do download
- `GET /api/downloads` - Lista todos os downloads
- `POST /api/downloads/{id}/start` - Inicia download do Google Drive
- `POST /api/downloads/{id}/pause` - Pausa download
- `POST /api/downloads/{id}/resume` - Retoma download
- `DELETE /api/downloads/{id}` - Remove download

### Frontend (React + Tailwind + Framer Motion)
- Interface com tema The Sims 4 (cores verdes, fundo escuro)
- Plumbob animado que muda de cor conforme status
- Barra de progresso com stripes animadas
- Cards de status (velocidade, tempo restante, tamanho, integridade)
- Animação de hash SHA-256 durante verificação
- Sistema de toasts para notificações

### Components
- `Plumbob.jsx` - Componente SVG animado do diamante do Sims
- `DownloadCard.jsx` - Card principal de download com controles
- `App.js` - Aplicação principal com lógica de estado

## Simulated Features (Demo Mode)
- Download progress is simulated (increments 1% every 0.5s)
- SHA-256 checksum is generated but verification is simulated
- Installation process is simulated

## Next Tasks
1. **Integração Real com Google Drive API** - Implementar download real usando Google Drive API
2. **Download em Chunks** - Implementar download em partes para suportar pause/resume real
3. **Verificação de Checksum Real** - Calcular SHA-256 real dos arquivos baixados
4. **Sistema de Extração** - Implementar extração de arquivos ZIP
5. **Instalador** - Criar instalador real que configura o jogo
6. **Histórico de Downloads** - Mostrar lista de downloads anteriores
7. **Configurações** - Permitir escolher pasta de destino
8. **Notificações Desktop** - Notificar quando download/instalação completar

## Tech Stack
- **Backend**: FastAPI, Motor (MongoDB async), aiohttp, google-api-python-client
- **Frontend**: React 19, Tailwind CSS, Framer Motion, Lucide Icons
- **Database**: MongoDB
- **Fonts**: Fredoka (headings), Quicksand (body), JetBrains Mono (code)
- **Google Drive**: API integration for public folder access

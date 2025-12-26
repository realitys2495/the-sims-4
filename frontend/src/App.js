import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import { Plumbob } from "./components/Plumbob";
import { DownloadCard } from "./components/DownloadCard";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent } from "./components/ui/card";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { 
  Gamepad2, 
  Sparkles, 
  Download as DownloadIcon,
  FolderOpen,
  Package
} from "lucide-react";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Link do Google Drive já configurado
const GOOGLE_DRIVE_URL = "https://drive.google.com/drive/folders/1CQVPFH5iGWJKcMRFf7ZKSjgPSxFw4ywF?usp=drive_link";

function App() {
  const [downloadPath, setDownloadPath] = useState("C:\\Users\\Downloads\\TheSims4");
  const [currentDownload, setCurrentDownload] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSetup, setShowSetup] = useState(true);

  // Poll for download status
  useEffect(() => {
    let interval;
    if (currentDownload?.id && ['downloading', 'verifying', 'extracting', 'installing'].includes(currentDownload.status)) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/downloads/${currentDownload.id}`);
          setCurrentDownload(response.data);
          
          if (response.data.status === 'completed') {
            toast.success("The Sims 4 instalado com sucesso!", {
              description: `Instalado em: ${downloadPath}`
            });
            clearInterval(interval);
          } else if (response.data.status === 'verified') {
            toast.success("Download verificado!", {
              description: "Extraindo arquivos..."
            });
          } else if (response.data.status === 'extracting') {
            toast.info("Extraindo arquivos ZIP...", {
              description: "Aguarde a extração completar"
            });
          }
        } catch (error) {
          console.error("Error fetching status:", error);
        }
      }, 500);
    }
    return () => clearInterval(interval);
  }, [currentDownload?.id, currentDownload?.status, downloadPath]);

  const handleStartDownload = async () => {
    if (!downloadPath.trim()) {
      toast.error("Por favor, escolha uma pasta de destino");
      return;
    }

    setIsLoading(true);
    try {
      // Criar download com link pré-configurado
      const response = await axios.post(`${API}/downloads`, {
        google_drive_url: GOOGLE_DRIVE_URL,
        filename: "TheSims4.zip",
        download_path: downloadPath
      });
      setCurrentDownload(response.data);
      setShowSetup(false);
      
      // Iniciar download automaticamente
      await axios.post(`${API}/downloads/${response.data.id}/start`);
      setCurrentDownload(prev => ({ ...prev, status: 'downloading' }));
      
      toast.success("Download iniciado!", {
        description: `Salvando em: ${downloadPath}`
      });
    } catch (error) {
      console.error("Error starting download:", error);
      toast.error("Erro ao iniciar download", {
        description: error.response?.data?.detail || "Tente novamente"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePause = async () => {
    if (!currentDownload?.id) return;
    try {
      await axios.post(`${API}/downloads/${currentDownload.id}/pause`);
      setCurrentDownload(prev => ({ ...prev, status: 'paused' }));
      toast.info("Download pausado");
    } catch (error) {
      console.error("Error pausing download:", error);
      toast.error("Erro ao pausar download");
    }
  };

  const handleResume = async () => {
    if (!currentDownload?.id) return;
    try {
      await axios.post(`${API}/downloads/${currentDownload.id}/resume`);
      setCurrentDownload(prev => ({ ...prev, status: 'downloading' }));
      toast.info("Download retomado!");
    } catch (error) {
      console.error("Error resuming download:", error);
      toast.error("Erro ao retomar download");
    }
  };

  const handleInstall = async () => {
    if (!currentDownload?.id) return;
    try {
      await axios.post(`${API}/downloads/${currentDownload.id}/install`);
      setCurrentDownload(prev => ({ ...prev, status: 'installing' }));
      toast.info("Instalação iniciada!");
    } catch (error) {
      console.error("Error installing:", error);
      toast.error("Erro ao iniciar instalação");
    }
  };

  const handleReset = () => {
    setCurrentDownload(null);
    setDownloadPath("C:\\Users\\Downloads\\TheSims4");
    setShowSetup(true);
  };

  return (
    <div className="min-h-screen bg-dark-void relative overflow-hidden noise-overlay" data-testid="app-container">
      <Toaster position="top-right" richColors />
      
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-sims-green/10 via-transparent to-sims-blue/5 pointer-events-none" />
      
      {/* Animated background elements */}
      <div className="absolute top-20 right-20 opacity-20">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
          <Sparkles className="w-32 h-32 text-sims-green" />
        </motion.div>
      </div>
      
      <div className="absolute bottom-20 left-20 opacity-10">
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        >
          <Gamepad2 className="w-48 h-48 text-sims-blue" />
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 py-12 max-w-5xl">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="flex justify-center mb-8">
            <Plumbob size={100} status={currentDownload?.status || 'idle'} />
          </div>
          
          <h1 className="font-heading text-5xl md:text-7xl font-bold text-white mb-4 tracking-tight">
            The Sims 4
          </h1>
          <p className="font-heading text-2xl md:text-3xl text-sims-green mb-2">
            Downloader
          </p>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Baixe e instale The Sims 4 diretamente do Google Drive com verificação de integridade
          </p>
        </motion.div>

        {/* Download Setup Section */}
        {showSetup && !currentDownload && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <Card className="glass border-white/10 max-w-2xl mx-auto mb-8" data-testid="setup-card">
              <CardContent className="p-8">
                {/* Info do arquivo */}
                <div className="flex items-center gap-3 mb-6 p-4 bg-sims-green/10 rounded-lg border border-sims-green/20">
                  <Package className="w-8 h-8 text-sims-green" />
                  <div>
                    <h3 className="font-heading text-lg text-white">The Sims 4 - Edição Completa</h3>
                    <p className="text-sm text-muted-foreground">76 GB • Arquivo ZIP • Será extraído automaticamente</p>
                  </div>
                </div>

                {/* Pasta de destino */}
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <FolderOpen className="w-5 h-5 text-sims-blue" />
                    <label className="font-heading text-lg text-white">Onde deseja instalar?</label>
                  </div>
                  
                  <Input
                    data-testid="download-path-input"
                    type="text"
                    placeholder="C:\Games\TheSims4"
                    value={downloadPath}
                    onChange={(e) => setDownloadPath(e.target.value)}
                    className="bg-surface-dark border-white/10 text-white placeholder:text-muted-foreground focus:border-sims-green focus:ring-sims-green font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    O jogo será baixado e extraído nesta pasta
                  </p>
                </div>

                {/* Botão de download */}
                <Button
                  data-testid="btn-start-download"
                  onClick={handleStartDownload}
                  disabled={isLoading}
                  className="w-full bg-sims-green hover:bg-sims-green-600 text-white font-heading px-8 py-6 text-lg neon-glow pulse-green"
                >
                  {isLoading ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="flex items-center gap-2"
                    >
                      <DownloadIcon className="w-6 h-6" />
                      <span>Preparando...</span>
                    </motion.div>
                  ) : (
                    <>
                      <DownloadIcon className="w-6 h-6 mr-2" />
                      Baixar The Sims 4
                    </>
                  )}
                </Button>

                <p className="text-xs text-center text-muted-foreground mt-4">
                  Ao clicar, o download iniciará automaticamente da nuvem
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Download Card */}
        {currentDownload && (
          <div className="mb-8">
            <DownloadCard
              download={currentDownload}
              downloadPath={downloadPath}
              onPause={handlePause}
              onResume={handleResume}
              onInstall={handleInstall}
            />
            
            {currentDownload.status === 'completed' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center mt-6"
              >
                <Button
                  data-testid="new-download-btn"
                  onClick={handleReset}
                  variant="outline"
                  className="border-white/20 text-white hover:bg-white/10"
                >
                  Novo Download
                </Button>
              </motion.div>
            )}
          </div>
        )}

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12"
        >
          <Card className="glass border-white/10 hover:border-sims-green/50 transition-colors" data-testid="feature-card-1">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-sims-green/20 flex items-center justify-center mx-auto mb-4">
                <DownloadIcon className="w-6 h-6 text-sims-green" />
              </div>
              <h3 className="font-heading text-lg text-white mb-2">Download Direto</h3>
              <p className="text-sm text-muted-foreground">
                Baixe diretamente da nuvem com suporte a pause/resume
              </p>
            </CardContent>
          </Card>

          <Card className="glass border-white/10 hover:border-sims-blue/50 transition-colors" data-testid="feature-card-2">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-sims-blue/20 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-sims-blue" />
              </div>
              <h3 className="font-heading text-lg text-white mb-2">Verificação SHA-256</h3>
              <p className="text-sm text-muted-foreground">
                Garante que seus arquivos estão íntegros e sem corrupção
              </p>
            </CardContent>
          </Card>

          <Card className="glass border-white/10 hover:border-amber-500/50 transition-colors" data-testid="feature-card-3">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center mx-auto mb-4">
                <Package className="w-6 h-6 text-amber-500" />
              </div>
              <h3 className="font-heading text-lg text-white mb-2">Extração Automática</h3>
              <p className="text-sm text-muted-foreground">
                O ZIP é extraído automaticamente na pasta escolhida
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center mt-16 text-muted-foreground text-sm"
        >
          <p>The Sims 4 Downloader • Feito com Sul Sul</p>
        </motion.footer>
      </div>
    </div>
  );
}

export default App;

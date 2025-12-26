import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Download, 
  Pause, 
  Play, 
  ShieldCheck, 
  Wifi, 
  HardDrive, 
  Clock,
  CheckCircle,
  Loader2,
  AlertCircle,
  Package
} from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Card, CardContent } from './ui/card';

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatSpeed = (bytesPerSecond) => {
  return formatBytes(bytesPerSecond) + '/s';
};

const HashAnimation = ({ hash, isCalculating }) => {
  const [displayHash, setDisplayHash] = useState('');
  
  useEffect(() => {
    if (isCalculating) {
      const chars = '0123456789abcdef';
      const interval = setInterval(() => {
        let randomHash = '';
        for (let i = 0; i < 64; i++) {
          randomHash += chars[Math.floor(Math.random() * chars.length)];
        }
        setDisplayHash(randomHash);
      }, 50);
      return () => clearInterval(interval);
    } else if (hash) {
      setDisplayHash(hash);
    }
  }, [isCalculating, hash]);

  return (
    <span className={`font-mono text-xs break-all ${isCalculating ? 'hash-calculating text-sims-blue' : 'text-sims-green'}`}>
      {displayHash || '---'}
    </span>
  );
};

export const DownloadCard = ({ download, downloadPath, onPause, onResume, onInstall }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const status = download?.status || 'idle';
  const progress = download?.progress || 0;
  const downloadedSize = download?.downloaded_size || 0;
  const totalSize = download?.total_size || 81604378624;
  const speed = download?.speed || 0;
  const eta = download?.eta || '--:--:--';
  const checksumStatus = download?.checksum_status || 'pending';
  const checksum = download?.checksum_calculated || '';

  const getStatusIcon = () => {
    switch (status) {
      case 'downloading':
        return <Loader2 className="w-5 h-5 animate-spin text-sims-green" />;
      case 'paused':
        return <Pause className="w-5 h-5 text-amber-500" />;
      case 'verifying':
        return <ShieldCheck className="w-5 h-5 animate-pulse text-sims-blue" />;
      case 'verified':
        return <CheckCircle className="w-5 h-5 text-sims-green" />;
      case 'installing':
        return <Package className="w-5 h-5 animate-bounce text-sims-blue" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-sims-green" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-sims-red" />;
      default:
        return <Download className="w-5 h-5 text-muted-foreground" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'downloading':
        return 'Baixando...';
      case 'paused':
        return 'Pausado';
      case 'verifying':
        return 'Verificando integridade...';
      case 'verified':
        return 'Verificado! Extraindo...';
      case 'extracting':
        return 'Extraindo arquivos ZIP...';
      case 'installing':
        return 'Finalizando instalação...';
      case 'completed':
        return 'Instalação concluída!';
      case 'error':
        return 'Erro no download';
      default:
        return 'Pronto para baixar';
    }
  };

  const getProgressColor = () => {
    switch (status) {
      case 'downloading':
        return 'bg-gradient-to-r from-sims-green to-teal-400';
      case 'paused':
        return 'bg-amber-500';
      case 'verifying':
        return 'bg-sims-blue';
      case 'verified':
      case 'completed':
        return 'bg-sims-green';
      case 'error':
        return 'bg-sims-red';
      default:
        return 'bg-muted';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      <Card className="glass border-white/10 overflow-hidden" data-testid="download-card">
        <CardContent className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <div>
                <h3 className="font-heading font-semibold text-lg text-white">
                  {download?.filename || 'The Sims 4'}
                </h3>
                <p className="text-sm text-muted-foreground">{getStatusText()}</p>
                {downloadPath && (
                  <p className="text-xs text-sims-blue font-mono mt-1">{downloadPath}</p>
                )}
              </div>
            </div>
            <div className="text-right">
              <p className="font-mono text-sm text-white">
                {formatBytes(downloadedSize)} / {formatBytes(totalSize)}
              </p>
              <p className="text-xs text-muted-foreground">
                {progress.toFixed(1)}% completo
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="relative mb-6" data-testid="progress-bar">
            <div className="h-6 bg-surface-dark rounded-full overflow-hidden border border-white/10">
              <motion.div
                className={`h-full ${getProgressColor()} ${status === 'downloading' ? 'progress-striped' : ''}`}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="font-mono text-sm font-bold text-white drop-shadow-lg">
                {progress.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="glass rounded-lg p-4 text-center">
              <Wifi className="w-5 h-5 mx-auto mb-2 text-sims-blue" />
              <p className="font-mono text-sm text-white">{formatSpeed(speed)}</p>
              <p className="text-xs text-muted-foreground">Velocidade</p>
            </div>
            <div className="glass rounded-lg p-4 text-center">
              <Clock className="w-5 h-5 mx-auto mb-2 text-sims-green" />
              <p className="font-mono text-sm text-white">{eta}</p>
              <p className="text-xs text-muted-foreground">Tempo restante</p>
            </div>
            <div className="glass rounded-lg p-4 text-center">
              <HardDrive className="w-5 h-5 mx-auto mb-2 text-amber-500" />
              <p className="font-mono text-sm text-white">{formatBytes(totalSize)}</p>
              <p className="text-xs text-muted-foreground">Tamanho total</p>
            </div>
            <div className="glass rounded-lg p-4 text-center">
              <ShieldCheck className={`w-5 h-5 mx-auto mb-2 ${
                checksumStatus === 'verified' ? 'text-sims-green' : 
                checksumStatus === 'calculating' ? 'text-sims-blue animate-pulse' : 
                'text-muted-foreground'
              }`} />
              <p className="font-mono text-sm text-white capitalize">
                {checksumStatus === 'pending' ? 'Pendente' : 
                 checksumStatus === 'calculating' ? 'Calculando...' : 
                 checksumStatus === 'verified' ? 'Verificado' : checksumStatus}
              </p>
              <p className="text-xs text-muted-foreground">Integridade</p>
            </div>
          </div>

          {/* Checksum Display */}
          <AnimatePresence>
            {(checksumStatus === 'calculating' || checksumStatus === 'verified') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-6 glass rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <ShieldCheck className={`w-4 h-4 ${checksumStatus === 'verified' ? 'text-sims-green' : 'text-sims-blue'}`} />
                  <span className="text-sm font-medium text-white">SHA-256 Checksum</span>
                </div>
                <HashAnimation 
                  hash={checksum} 
                  isCalculating={checksumStatus === 'calculating'} 
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-center">
            {status === 'downloading' && (
              <Button
                data-testid="btn-pause"
                onClick={onPause}
                variant="outline"
                className="border-amber-500 text-amber-500 hover:bg-amber-500/10 px-8 py-6 text-lg font-heading"
              >
                <Pause className="w-5 h-5 mr-2" />
                Pausar
              </Button>
            )}

            {status === 'paused' && (
              <Button
                data-testid="btn-resume"
                onClick={onResume}
                className="bg-sims-green hover:bg-sims-green-600 text-white px-8 py-6 text-lg font-heading neon-glow"
              >
                <Play className="w-5 h-5 mr-2" />
                Continuar
              </Button>
            )}

            {status === 'verified' && (
              <div className="flex items-center gap-2 text-sims-blue">
                <Package className="w-6 h-6 animate-bounce" />
                <span className="font-heading text-lg">Extraindo arquivos...</span>
              </div>
            )}

            {status === 'extracting' && (
              <div className="flex items-center gap-2 text-sims-blue">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="font-heading text-lg">Extraindo The Sims 4...</span>
              </div>
            )}

            {status === 'completed' && (
              <div className="flex items-center gap-2 text-sims-green">
                <CheckCircle className="w-8 h-8" />
                <span className="font-heading text-xl">The Sims 4 instalado com sucesso!</span>
              </div>
            )}

            {status === 'installing' && (
              <div className="flex items-center gap-2 text-sims-blue">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="font-heading text-lg">Finalizando instalação...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default DownloadCard;

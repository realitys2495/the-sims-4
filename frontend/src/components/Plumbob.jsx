import React from 'react';
import { motion } from 'framer-motion';

export const Plumbob = ({ size = 120, status = 'idle', className = '' }) => {
  const getColor = () => {
    switch (status) {
      case 'downloading':
      case 'verified':
      case 'completed':
        return '#10A316'; // Green
      case 'paused':
        return '#F59E0B'; // Amber
      case 'error':
        return '#E4002B'; // Red
      case 'verifying':
        return '#00A4E4'; // Blue
      default:
        return '#4C9F38'; // Plumbob green
    }
  };

  const color = getColor();

  return (
    <motion.div
      className={`relative ${className}`}
      animate={{
        y: [0, -20, 0],
        rotate: [0, 5, 0, -5, 0],
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      style={{ width: size, height: size * 1.5 }}
    >
      {/* Glow effect */}
      <div
        className="absolute inset-0 blur-xl opacity-60"
        style={{
          background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
        }}
      />
      
      {/* Top pyramid */}
      <svg
        viewBox="0 0 100 150"
        className="absolute inset-0 w-full h-full"
        style={{
          filter: `drop-shadow(0 0 20px ${color})`,
        }}
      >
        {/* Top diamond */}
        <polygon
          points="50,0 100,50 50,100 0,50"
          fill={color}
          opacity="0.9"
        />
        {/* Left face highlight */}
        <polygon
          points="50,0 0,50 50,100"
          fill={color}
          opacity="0.7"
        />
        {/* Right face */}
        <polygon
          points="50,0 100,50 50,100"
          fill={color}
          opacity="1"
        />
        {/* Highlight */}
        <polygon
          points="50,10 85,50 50,90"
          fill="white"
          opacity="0.15"
        />
        
        {/* Bottom extension */}
        <polygon
          points="50,100 75,75 75,110 50,135 25,110 25,75"
          fill={color}
          opacity="0.8"
        />
      </svg>
      
      {/* Inner glow */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-1/2 h-1/2 rounded-full"
        style={{
          background: `radial-gradient(circle, white 0%, ${color} 50%, transparent 70%)`,
          opacity: 0.3,
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </motion.div>
  );
};

export default Plumbob;

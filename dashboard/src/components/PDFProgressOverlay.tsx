import React from 'react';
import { Loader2, XCircle } from 'lucide-react';

interface PDFProgressOverlayProps {
  progress: number;
  onCancel: () => void;
}

export const PDFProgressOverlay: React.FC<PDFProgressOverlayProps> = ({ progress, onCancel }) => {
  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-gray-950/60 backdrop-blur-sm transition-opacity duration-300">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 max-w-sm w-full shadow-2xl flex flex-col items-center animate-in zoom-in-95 duration-200">
        <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mb-6">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
        
        <h3 className="text-xl font-bold text-gray-100 mb-2">Generating PDF...</h3>
        <p className="text-sm text-gray-400 text-center mb-8">
          Please wait while we format your report. This may take a moment for long conversations.
        </p>

        {/* Progress Bar Container */}
        <div className="w-full bg-gray-800 rounded-full h-3 mb-2 overflow-hidden shadow-inner border border-gray-700/50">
          <div 
            className="bg-gradient-to-r from-blue-600 to-blue-400 h-full rounded-full transition-all duration-300 ease-out relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute inset-0 bg-white/20 w-full h-full animate-[shimmer_2s_infinite] -skew-x-12"></div>
          </div>
        </div>
        
        <div className="flex justify-between w-full text-xs font-medium text-gray-500 mb-8">
          <span>Processing</span>
          <span>{progress}%</span>
        </div>

        <button 
          onClick={onCancel}
          className="flex items-center gap-2 px-6 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl transition-colors font-medium text-sm group"
        >
          <XCircle className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Cancel Export
        </button>
      </div>
    </div>
  );
};

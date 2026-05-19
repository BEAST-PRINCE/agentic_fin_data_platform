import { Bug, Play, Square, Settings } from 'lucide-react';

export function ScraperSidebar() {
  return (
    <aside className="w-72 bg-gray-950 border-r border-gray-800/60 p-6 hidden lg:flex flex-col">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-indigo-500/20 rounded-lg">
          <Bug className="w-6 h-6 text-indigo-400" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-200">Scraper Ops</h2>
          <p className="text-xs text-gray-500">Phase 9 Preview</p>
        </div>
      </div>

      <div className="space-y-6 flex-1">
        
        {/* Placeholder Spider 1 */}
        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-800 opacity-50 cursor-not-allowed group">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-300">mint_companies</span>
            <span className="flex h-2 w-2 rounded-full bg-red-500"></span>
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded flex items-center justify-center pointer-events-none">
              <Play className="w-4 h-4" />
            </button>
            <button className="flex-1 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded flex items-center justify-center pointer-events-none">
              <Square className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Placeholder Spider 2 */}
        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-800 opacity-50 cursor-not-allowed group">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-300">fe_markets</span>
            <span className="flex h-2 w-2 rounded-full bg-red-500"></span>
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded flex items-center justify-center pointer-events-none">
              <Play className="w-4 h-4" />
            </button>
            <button className="flex-1 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded flex items-center justify-center pointer-events-none">
              <Square className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

      <div className="mt-auto pt-6 border-t border-gray-800/60 opacity-50">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Settings className="w-4 h-4" /> Operations locked
        </div>
        <p className="text-xs text-gray-600 mt-2 leading-relaxed">
          Spider controls and advanced metrics will be activated in Phase 9.
        </p>
      </div>
    </aside>
  );
}

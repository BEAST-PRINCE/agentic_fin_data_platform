import { useState, useEffect } from 'react';
import { Bug, Play, Square, Terminal as TerminalIcon, X } from 'lucide-react';

interface ScraperStatus {
  name: string;
  status: 'Running' | 'Idle';
  pid: number | null;
}

interface PipelineStatus {
  active_stage: string;
  status: string;
}

export function ScraperSidebar() {
  const [scrapers, setScrapers] = useState<ScraperStatus[]>([]);
  const [pipeline, setPipeline] = useState<PipelineStatus>({ active_stage: 'idle', status: 'Idle' });
  const [loading, setLoading] = useState(true);
  const [selectedLogs, setSelectedLogs] = useState<{type: 'scraper' | 'pipeline', name: string} | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);
  const [logWidth, setLogWidth] = useState(600);

  const startResize = (e: React.MouseEvent) => {
    const startX = e.clientX;
    const startWidth = logWidth;

    const doDrag = (dragEvent: MouseEvent) => {
      setLogWidth(Math.max(400, Math.min(window.innerWidth - 300, startWidth + (startX - dragEvent.clientX))));
    };

    const stopDrag = () => {
      document.removeEventListener('mousemove', doDrag);
      document.removeEventListener('mouseup', stopDrag);
      document.body.style.cursor = 'default';
    };

    document.body.style.cursor = 'col-resize';
    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);
  };

  const fetchStatuses = () => {
    Promise.all([
      fetch('/api/scrapers').then(res => res.json()),
      fetch('/api/pipeline/status').then(res => res.json())
    ])
      .then(([scrapersData, pipelineData]) => {
        setScrapers(scrapersData);
        setPipeline(prev => {
          if (prev.active_stage === 'gold' && pipelineData.active_stage !== 'gold') {
            window.dispatchEvent(new Event('goldStageCompleted'));
          }
          if (prev.active_stage !== 'idle' && pipelineData.active_stage === 'idle') {
            window.dispatchEvent(new Event('pipelineCompleted'));
          }
          return pipelineData;
        });
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch operations status:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchStatuses();
    // Increased polling gap duration to reduce API load
    const interval = setInterval(fetchStatuses, 10000);
    return () => clearInterval(interval);
  }, []);

  // Poll logs
  useEffect(() => {
    if (!selectedLogs) {
      setPolling(false);
      return;
    }

    const fetchLogs = () => {
      const endpoint = selectedLogs.type === 'scraper' 
        ? `/api/scrapers/${selectedLogs.name}/logs`
        : `/api/pipeline/logs?stage=${selectedLogs.name}`;
        
      fetch(endpoint)
        .then(res => res.json())
        .then(data => {
          if (data.logs) {
            setLogs(data.logs);
          }
        });
    };

    // Immediately clear logs when switching views so old logs don't flash
    setLogs([]);
    fetchLogs();
    setPolling(true);
    // Increased polling gap duration to reduce API load
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, [selectedLogs]);

  const startScraper = async (name: string) => {
    try {
      await fetch(`/api/scrapers/${name}/start`, { method: 'POST' });
      fetchStatuses();
    } catch (e) { console.error(e); }
  };

  const stopScraper = async (name: string) => {
    try {
      await fetch(`/api/scrapers/${name}/stop`, { method: 'POST' });
      fetchStatuses();
    } catch (e) { console.error(e); }
  };
  
  const startPipeline = async (stage: string) => {
    try {
      await fetch(`/api/pipeline/run/${stage}`, { method: 'POST' });
      fetchStatuses();
    } catch (e) { console.error(e); }
  };
  
  const stopPipeline = async () => {
    try {
      await fetch(`/api/pipeline/stop`, { method: 'POST' });
      fetchStatuses();
    } catch (e) { console.error(e); }
  };

  const pipelineStages = [
    { id: 'silver', label: 'Silver Layer (Clean)' },
    { id: 'gold', label: 'Gold Layer (ML/Agg)' },
    { id: 'indexer', label: 'Vector Indexer' }
  ];

  return (
    <>
      <aside className="w-72 bg-black border-r border-gray-800 flex flex-col p-4 shadow-xl z-10 relative">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-indigo-500/10 rounded-lg">
            <Bug className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-200">Ops Center</h2>
            <p className="text-xs text-gray-500">Live Mission Control</p>
          </div>
        </div>

        <div className="space-y-6 flex-1">
          {/* Scrapers Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Web Scrapers</h3>
            {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-24 bg-gray-900 rounded-lg"></div>
              <div className="h-24 bg-gray-900 rounded-lg"></div>
            </div>
          ) : (
            scrapers.map(scraper => {
              const isRunning = scraper.status === 'Running';
              return (
                <div key={scraper.name} className={`p-4 rounded-lg border transition-colors ${isRunning ? 'bg-gray-900 border-indigo-500/50' : 'bg-gray-900/50 border-gray-800'}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-300 truncate pr-2" title={scraper.name}>{scraper.name}</span>
                    <span className="relative flex h-2.5 w-2.5 shrink-0">
                      {isRunning && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                      <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isRunning ? 'bg-emerald-500' : 'bg-gray-600'}`}></span>
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => isRunning ? stopScraper(scraper.name) : startScraper(scraper.name)}
                      className={`flex-1 py-1.5 rounded flex items-center justify-center transition-colors ${
                        isRunning 
                          ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400' 
                          : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400'
                      }`}
                      title={isRunning ? "Stop Scraper" : "Start Scraper"}
                    >
                      {isRunning ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button 
                      onClick={() => setSelectedLogs(
                        selectedLogs?.type === 'scraper' && selectedLogs.name === scraper.name 
                          ? null 
                          : {type: 'scraper', name: scraper.name}
                      )}
                      className={`flex-1 py-1.5 rounded flex items-center justify-center transition-colors ${
                        selectedLogs?.type === 'scraper' && selectedLogs.name === scraper.name ? 'bg-indigo-500 text-white' : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
                      }`}
                      title="View Logs"
                    >
                      <TerminalIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
          </div>
          
          {/* Pipeline Section */}
          <div className="space-y-3 border-t border-gray-800/60 pt-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Data Pipeline</h3>
            {pipelineStages.map(stage => {
              const isRunning = pipeline.active_stage === stage.id;
              const isDisabled = pipeline.active_stage !== 'idle' && !isRunning;
              
              return (
                <div key={stage.id} className={`p-4 rounded-lg border transition-colors ${isRunning ? 'bg-gray-900 border-emerald-500/50' : 'bg-gray-900/50 border-gray-800'} ${isDisabled ? 'opacity-50' : ''}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-300 pr-2">{stage.label}</span>
                    <span className="relative flex h-2.5 w-2.5 shrink-0">
                      {isRunning && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                      <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isRunning ? 'bg-emerald-500' : 'bg-gray-600'}`}></span>
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => isRunning ? stopPipeline() : startPipeline(stage.id)}
                      disabled={isDisabled}
                      className={`flex-1 py-1.5 rounded flex items-center justify-center transition-colors ${
                        isDisabled ? 'bg-gray-800 text-gray-600 cursor-not-allowed' :
                        isRunning 
                          ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400' 
                          : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400'
                      }`}
                      title={isRunning ? "Stop Stage" : "Run Stage"}
                    >
                      {isRunning ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button 
                      onClick={() => setSelectedLogs(
                        selectedLogs?.type === 'pipeline' && selectedLogs.name === stage.id 
                          ? null 
                          : {type: 'pipeline', name: stage.id}
                      )}
                      className={`flex-1 py-1.5 rounded flex items-center justify-center transition-colors ${
                        selectedLogs?.type === 'pipeline' && selectedLogs.name === stage.id ? 'bg-emerald-500 text-white' : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
                      }`}
                      title="View Logs"
                    >
                      <TerminalIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </aside>

      {/* Terminal Slide-out Overlay */}
      {selectedLogs && (
        <div 
          className="fixed top-0 bottom-0 right-0 max-w-full bg-gray-950 border-l border-gray-800 shadow-2xl z-50 flex flex-col transform transition-transform"
          style={{ width: `${logWidth}px` }}
        >
          {/* Resize Handle */}
          <div 
            className="absolute top-0 bottom-0 left-0 w-2 cursor-col-resize hover:bg-indigo-500/50 z-50 -ml-1"
            onMouseDown={startResize}
          />
          <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/80">
            <div className="flex items-center gap-2">
              <TerminalIcon className="w-5 h-5 text-indigo-400" />
              <h3 className="text-gray-200 font-medium font-mono text-sm">{selectedLogs.name} Logs</h3>
              {polling && <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse ml-2"></span>}
            </div>
            <button onClick={() => setSelectedLogs(null)} className="text-gray-400 hover:text-white p-1">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 bg-[#0d1117]">
            {logs.length === 0 ? (
              <div className="text-gray-500 italic text-sm font-mono">
                {selectedLogs.type === 'pipeline' ? "No logs available for this pipeline stage..." : "No logs available for this spider..."}
              </div>
            ) : (
              <pre className="text-xs text-green-400 font-mono leading-relaxed break-all whitespace-pre-wrap">
                {logs.join('\n')}
              </pre>
            )}
          </div>
        </div>
      )}
    </>
  );
}

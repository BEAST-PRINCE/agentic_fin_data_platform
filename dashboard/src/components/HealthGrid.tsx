import { useEffect, useState } from 'react';
import { DatabaseZap, FileJson, Layers, ArrowRight } from 'lucide-react';

interface Stats {
  bronze: { raw_messages: number };
  silver: { cleaned_articles: number };
  gold: { serving_articles: number };
}

interface ComponentHealth {
  status: 'online' | 'offline';
  latency_ms: number | null;
  error?: string;
}

interface SystemHealth {
  minio: ComponentHealth;
  kafka: ComponentHealth;
  qdrant: ComponentHealth;
  duckdb: ComponentHealth;
  ollama: ComponentHealth;
}

export function HealthGrid() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = () => {
      Promise.all([
        fetch('/api/system/statistics').then(res => res.json()),
        fetch('/api/health').then(res => res.json())
      ])
        .then(([statsData, healthData]) => {
          setStats(statsData);
          setHealth(healthData);
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to fetch dashboard data:", err);
          setLoading(false);
        });
    };

    fetchHealth();
    
    window.addEventListener('pipelineCompleted', fetchHealth);
    return () => window.removeEventListener('pipelineCompleted', fetchHealth);
  }, []);

  if (loading) return <div className="glass-panel p-6 animate-pulse h-32"></div>;

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center gap-2 mb-6">
        <DatabaseZap className="w-5 h-5 text-purple-400" />
        <h2 className="text-lg font-semibold text-gray-200">Lakehouse Throughput</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        {/* Bronze */}
        <div className="bg-gray-900/50 rounded-lg p-5 border border-amber-500/20 relative group hover:border-amber-500/50 transition-colors">
          <div className="text-sm font-medium text-amber-500 mb-1 flex items-center gap-2">
            <FileJson className="w-4 h-4" /> Bronze Layer
          </div>
          <div className="text-3xl font-bold text-gray-100">{stats?.bronze.raw_messages.toLocaleString() || 0}</div>
          <div className="text-xs text-gray-500 mt-1">Raw JSON Events</div>
          
          <ArrowRight className="absolute -right-5 top-1/2 -translate-y-1/2 text-gray-600 hidden md:block" />
        </div>

        {/* Silver */}
        <div className="bg-gray-900/50 rounded-lg p-5 border border-gray-400/20 relative group hover:border-gray-400/50 transition-colors">
          <div className="text-sm font-medium text-gray-400 mb-1 flex items-center gap-2">
            <Layers className="w-4 h-4" /> Silver Layer
          </div>
          <div className="text-3xl font-bold text-gray-100">{stats?.silver.cleaned_articles.toLocaleString() || 0}</div>
          <div className="text-xs text-gray-500 mt-1">Cleaned Parquet Records</div>

          <ArrowRight className="absolute -right-5 top-1/2 -translate-y-1/2 text-gray-600 hidden md:block" />
        </div>

        {/* Gold */}
        <div className="bg-gray-900/50 rounded-lg p-5 border border-yellow-500/20 group hover:border-yellow-500/50 transition-colors">
          <div className="text-sm font-medium text-yellow-500 mb-1 flex items-center gap-2">
            <DatabaseZap className="w-4 h-4" /> Gold Layer
          </div>
          <div className="text-3xl font-bold text-gray-100">{stats?.gold.serving_articles.toLocaleString() || 0}</div>
          <div className="text-xs text-gray-500 mt-1">Serving Articles</div>
        </div>
      </div>

      {/* Infrastructure Health Row */}
      {health && (
        <div className="mt-8 pt-6 border-t border-gray-800">
          <div className="flex flex-wrap gap-4">
            {Object.entries(health).map(([key, info]) => (
              <div key={key} className="flex items-center gap-3 bg-gray-900/60 border border-gray-800 rounded-full px-4 py-2">
                <span className="relative flex h-2.5 w-2.5">
                  {info.status === 'online' && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                  <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${info.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                </span>
                <span className="text-sm font-medium text-gray-300 capitalize">{key}</span>
                {info.latency_ms && <span className="text-xs text-gray-500 font-mono ml-2">{info.latency_ms}ms</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { DatabaseZap, FileJson, Layers, ArrowRight } from 'lucide-react';

interface Stats {
  bronze: { raw_messages: number };
  silver: { cleaned_articles: number };
  gold: { serving_articles: number };
}

export function HealthGrid() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/system/statistics')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch stats:", err);
        setLoading(false);
      });
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
    </div>
  );
}

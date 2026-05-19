import { useEffect, useState } from 'react';
import { TrendingUp, BarChart3 } from 'lucide-react';

interface Trend {
  publish_date: string;
  source_domain: string;
  category: string;
  total_articles: number;
}

interface AggregatedTrend {
  source_domain: string;
  total_articles: number;
}

export function TrendingRadar() {
  const [trends, setTrends] = useState<AggregatedTrend[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/trending?start_date=2020-01-01&end_date=2030-01-01`)
      .then(res => res.json())
      .then(data => {
        // Aggregate totals per source domain
        const domainMap: { [key: string]: number } = {};
        data.forEach((item: Trend) => {
          if (item.source_domain) {
            domainMap[item.source_domain] = (domainMap[item.source_domain] || 0) + item.total_articles;
          }
        });
        
        const aggregated = Object.entries(domainMap)
          .map(([source_domain, total_articles]) => ({
            source_domain,
            total_articles
          }))
          .sort((a, b) => b.total_articles - a.total_articles);

        setTrends(aggregated.slice(0, 6));
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="glass-panel p-6 flex-1 flex flex-col">
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp className="w-5 h-5 text-rose-400" />
        <h2 className="text-lg font-semibold text-gray-200">Domain Throughput</h2>
      </div>

      <div className="flex-1 flex flex-col gap-4">
        {loading ? (
          <div className="animate-pulse space-y-4">
            {[1,2,3].map(i => <div key={i} className="h-10 bg-gray-800 rounded"></div>)}
          </div>
        ) : trends.length > 0 ? (
          trends.map((t, idx) => {
            // Calculate a fake percentage relative to the first item for the bar width
            const max = trends[0].total_articles;
            const pct = Math.max(10, Math.round((t.total_articles / max) * 100));
            return (
              <div key={idx} className="relative">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span className="font-medium text-gray-300">{t.source_domain}</span>
                  <span>{t.total_articles} articles</span>
                </div>
                <div className="w-full bg-gray-900 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-rose-500 to-orange-400 h-full rounded-full"
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center text-gray-500 m-auto">
            <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
            No trend data available
          </div>
        )}
      </div>
    </div>
  );
}

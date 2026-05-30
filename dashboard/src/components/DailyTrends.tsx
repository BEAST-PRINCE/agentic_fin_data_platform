import { useEffect, useState } from 'react';
import { Calendar, Hash, AlertCircle } from 'lucide-react';

interface EntityTrend {
  entity_name: string;
  entity_type: string;
  total_mentions: number;
}

export function DailyTrends() {
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [entities, setEntities] = useState<EntityTrend[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch available dates on mount
  useEffect(() => {
    fetch('/api/trends/dates')
      .then(res => res.json())
      .then(dates => {
        if (dates && dates.length > 0) {
          setAvailableDates(dates);
          setSelectedDate(dates[0]); // Default to latest date
        }
      })
      .catch(err => console.error("Failed to fetch dates:", err));
  }, []);

  // Fetch trending entities when selectedDate changes
  useEffect(() => {
    if (!selectedDate) return;
    
    setLoading(true);
    fetch(`/entities?publish_date=${selectedDate}&limit=10`)
      .then(res => res.json())
      .then(data => {
        setEntities(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch entity trends:", err);
        setEntities([]);
        setLoading(false);
      });
  }, [selectedDate]);

  return (
    <div className="glass-panel p-6 flex-1 flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Hash className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-gray-200">Trending Topics</h2>
        </div>
        
        {/* Date Dropdown */}
        <div className="relative">
          <select 
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="appearance-none bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full pl-8 pr-8 py-1.5 cursor-pointer outline-none hover:bg-gray-800 transition-colors"
          >
            {availableDates.length === 0 ? (
              <option value="">No dates available</option>
            ) : (
              availableDates.map(date => (
                <option key={date} value={date}>{date}</option>
              ))
            )}
          </select>
          <Calendar className="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 transform -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-3 min-h-[200px]">
        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1,2,3,4,5].map(i => <div key={i} className="h-8 bg-gray-800 rounded"></div>)}
          </div>
        ) : entities.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {entities.map((t, idx) => {
              // Color based on entity type
              let colorClass = "bg-gray-800 text-gray-300 border-gray-700";
              if (t.entity_type === "ORG") colorClass = "bg-blue-900/30 text-blue-300 border-blue-800/50";
              if (t.entity_type === "PERSON") colorClass = "bg-emerald-900/30 text-emerald-300 border-emerald-800/50";
              if (t.entity_type === "LOC" || t.entity_type === "GPE") colorClass = "bg-rose-900/30 text-rose-300 border-rose-800/50";
              
              return (
                <div key={idx} className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm ${colorClass}`}>
                  <span className="font-medium">{t.entity_name}</span>
                  <span className="text-xs opacity-75 bg-black/20 px-1.5 rounded-full">{t.total_mentions}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-gray-500 h-full flex-1 gap-2 mt-8">
            <AlertCircle className="w-8 h-8 opacity-50" />
            <p className="text-sm">No trending data for this day.</p>
          </div>
        )}
      </div>
    </div>
  );
}

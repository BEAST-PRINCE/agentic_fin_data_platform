import { useEffect, useState, useRef } from 'react';
import { Calendar as CalendarIcon, Hash, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';

interface EntityTrend {
  entity_name: string;
  entity_type: string;
  total_mentions: number;
}

export function DailyTrends() {
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [entities, setEntities] = useState<EntityTrend[]>([]);
  const [loading, setLoading] = useState(true);

  // Calendar specific state
  const [showCalendar, setShowCalendar] = useState(false);
  const [viewDate, setViewDate] = useState(new Date());
  const calendarRef = useRef<HTMLDivElement>(null);

  // Close calendar on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (calendarRef.current && !calendarRef.current.contains(event.target as Node)) {
        setShowCalendar(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Sync calendar view month with selectedDate when loaded
  useEffect(() => {
    if (selectedDate) {
      const [y, m, d] = selectedDate.split('-').map(Number);
      setViewDate(new Date(y, m - 1, d));
    }
  }, [selectedDate]);

  // Fetch available dates on mount
  const fetchAvailableDates = () => {
    fetch('/api/trends/dates')
      .then(res => res.json())
      .then(dates => {
        if (dates && dates.length > 0) {
          setAvailableDates(dates);
          setSelectedDate(dates[0]); // Default to latest date
        } else {
          setLoading(false);
        }
      })
      .catch(err => {
        console.error("Failed to fetch dates:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchAvailableDates();
  }, []);

  // Listen for Gold stage completion to refresh dates without polling
  useEffect(() => {
    const handleGoldComplete = () => {
      console.log("Gold stage completed! Refreshing trending topics...");
      fetchAvailableDates();
    };
    
    window.addEventListener('goldStageCompleted', handleGoldComplete);
    return () => window.removeEventListener('goldStageCompleted', handleGoldComplete);
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

  // Calendar render logic
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const handlePrevMonth = () => setViewDate(new Date(year, month - 1, 1));
  const handleNextMonth = () => setViewDate(new Date(year, month + 1, 1));

  const formatDate = (y: number, m: number, d: number) => {
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${y}-${pad(m + 1)}-${pad(d)}`;
  };

  return (
    <div className="glass-panel p-6 flex-1 flex flex-col relative z-20">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Hash className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-gray-200">Trending Topics</h2>
        </div>

        {/* Custom Calendar Dropdown */}
        <div className="relative" ref={calendarRef}>
          <button
            onClick={() => setShowCalendar(!showCalendar)}
            disabled={loading}
            className={`flex items-center gap-2 border text-sm rounded-lg transition-colors px-4 py-2 outline-none focus:ring-1 focus:ring-purple-500 ${
              loading 
                ? 'bg-gray-900/50 border-gray-800 text-gray-500 cursor-not-allowed' 
                : 'bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800'
            }`}
          >
            <CalendarIcon className={`w-4 h-4 ${loading ? 'text-gray-600' : 'text-purple-400'}`} />
            <span className="font-medium tracking-wide">{selectedDate || "Select Date"}</span>
          </button>

          {showCalendar && (
            <div className="absolute right-0 top-full mt-2 w-[280px] bg-gray-900 border border-gray-700 rounded-xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.8)] z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
              {/* Calendar Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-950/50">
                <button onClick={handlePrevMonth} className="p-1 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white">
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <div className="font-semibold text-gray-200 text-sm">
                  {monthNames[month]} {year}
                </div>
                <button onClick={handleNextMonth} className="p-1 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white">
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>

              {/* Calendar Grid */}
              <div className="p-4">
                <div className="grid grid-cols-7 gap-1 mb-2">
                  {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                    <div key={day} className="text-center text-[10px] font-bold tracking-wider text-gray-500 py-1 uppercase">
                      {day}
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-7 gap-1">
                  {Array.from({ length: firstDay }).map((_, i) => (
                    <div key={`empty-${i}`} className="p-2"></div>
                  ))}
                  {Array.from({ length: daysInMonth }).map((_, i) => {
                    const day = i + 1;
                    const dateStr = formatDate(year, month, day);
                    const isAvailable = availableDates.includes(dateStr);
                    const isSelected = selectedDate === dateStr;

                    return (
                      <div key={day} className="flex justify-center items-center p-0.5">
                        <button
                          disabled={!isAvailable}
                          onClick={() => {
                            setSelectedDate(dateStr);
                            setShowCalendar(false);
                          }}
                          className={`
                            w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all
                            ${!isAvailable ? 'text-gray-700 cursor-not-allowed opacity-30' : 'cursor-pointer hover:bg-gray-700 text-gray-300'}
                            ${isSelected ? 'bg-purple-600 !text-white hover:bg-purple-500 font-bold shadow-lg shadow-purple-500/40 ring-2 ring-purple-500/20' : ''}
                          `}
                        >
                          {day}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
              {/* Footer text */}
              <div className="p-3 border-t border-gray-800 bg-gray-950/30 text-xs text-center text-gray-500 flex items-center justify-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-purple-500/50"></div>
                Dates with active data
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-3 min-h-[200px]">
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          </div>
        ) : entities.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {entities.map((t, idx) => {
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

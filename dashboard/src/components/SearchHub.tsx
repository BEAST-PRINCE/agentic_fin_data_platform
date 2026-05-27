import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Loader2, Sparkles, ExternalLink } from 'lucide-react';

interface SearchResult {
  article_id: string;
  score: number;
  title: string;
  source_domain: string;
  publish_timestamp: string;
  source_tags: string[];
  semantic_keywords: string[];
}

export function SearchHub() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const res = await fetch(`/search?query=${encodeURIComponent(query)}&limit=5`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-200">Semantic Vector Search</h2>
        </div>
        <div className="text-xs text-gray-500 bg-gray-900/50 px-2 py-1 rounded">Powered by Qdrant</div>
      </div>

      <form onSubmit={handleSearch} className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-blue-500" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="glass-input block w-full pl-10 pr-24 py-4 text-lg bg-gray-900/60 text-white placeholder-gray-500"
          placeholder="Search semantic concepts (e.g., 'interest rate hikes', 'tech layoffs')..."
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="absolute right-2 top-2 bottom-2 px-6 bg-blue-600 hover:bg-blue-500 text-white rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Search"}
        </button>
      </form>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <span className="text-gray-500 animate-pulse">Computing vector distances...</span>
          </div>
        ) : results.length > 0 ? (
          results.map((hit, idx) => (
            <div key={idx} className="p-4 bg-gray-900/40 rounded-lg border border-gray-700/50 hover:border-blue-500/30 transition-all group">
              <div className="flex justify-between items-start mb-2">
                <Link 
                  to={`/article/${hit.article_id}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="font-semibold text-gray-200 hover:text-blue-400 hover:underline transition-all leading-tight cursor-pointer"
                >
                  {hit.title}
                </Link>
                <span className="text-xs font-mono px-2 py-1 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20 whitespace-nowrap ml-4">
                  {(hit.score * 100).toFixed(1)}% Match
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-400 mb-3">
                <span className="flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" /> {hit.source_domain}
                </span>
                <span>•</span>
                <span>{new Date(hit.publish_timestamp).toLocaleDateString()}</span>
              </div>
              <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-gray-800/50">
                <div className="flex flex-wrap gap-2">
                  {hit.source_tags?.slice(0, 3).map((tag, i) => (
                    <span key={i} className="px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                      {tag}
                    </span>
                  ))}
                </div>
                {hit.semantic_keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-2 border-l border-gray-700 pl-2 ml-1">
                    {hit.semantic_keywords?.slice(0, 3).map((kw, i) => (
                      <span key={i} className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        ) : hasSearched ? (
          <div className="text-center text-gray-500 mt-10">No semantic matches found.</div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 opacity-50">
            <Sparkles className="w-12 h-12 mb-3" />
            <p>Query the datalake using natural language</p>
          </div>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, Clock } from 'lucide-react';

interface Article {
  article_id: string;
  title: string;
  source_domain: string;
  publish_timestamp: string;
}

export function LiveFeed() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchArticles = () => {
      fetch('/articles?limit=8')
        .then(res => res.json())
        .then(data => {
          setArticles(data);
          setLoading(false);
        })
        .catch(err => console.error(err));
    };

    fetchArticles();
    // Poll every 30 seconds for new articles
    const interval = setInterval(fetchArticles, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center gap-2 mb-6">
        <Activity className="w-5 h-5 text-emerald-400" />
        <h2 className="text-lg font-semibold text-gray-200">Latest Ingested Articles</h2>
        <div className="ml-auto flex items-center gap-2 text-xs text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Live Feed
        </div>
      </div>

      {loading ? (
        <div className="flex space-x-4 animate-pulse overflow-hidden">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex-shrink-0 w-64 h-24 bg-gray-800 rounded-lg"></div>
          ))}
        </div>
      ) : (
        <div className="flex overflow-x-auto pb-4 gap-4 snap-x hide-scrollbar">
          {articles.map((article, idx) => (
            <div key={idx} className="flex-shrink-0 w-80 p-4 bg-gray-900/40 rounded-lg border border-gray-700/50 snap-start hover:bg-gray-800/60 transition-colors">
              <div className="text-xs text-gray-400 mb-2 flex items-center justify-between">
                <span className="px-2 py-0.5 bg-gray-800 rounded text-gray-300">{article.source_domain}</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(article.publish_timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
              </div>
              <Link 
                to={`/article/${article.article_id}`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm font-medium text-gray-200 line-clamp-2 leading-snug hover:text-blue-400 hover:underline transition-colors block cursor-pointer"
              >
                {article.title}
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

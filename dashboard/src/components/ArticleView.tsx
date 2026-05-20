import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, Globe, Code, FileText, Loader2 } from 'lucide-react';

interface FullArticle {
  article_id: string;
  title: string;
  clean_content?: string;
  content?: string;
  source_domain: string;
  publish_timestamp: string;
  extracted_keywords?: string[];
  summary?: string;
  category?: string;
  author?: string;
  [key: string]: any; // Allow for other fields in raw data
}

export function ArticleView() {
  const { articleId } = useParams();
  const [article, setArticle] = useState<FullArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    if (!articleId) return;
    
    setLoading(true);
    fetch(`/articles/${articleId}`)
      .then(res => {
        if (!res.ok) throw new Error("Article not found");
        return res.json();
      })
      .then(data => {
        setArticle(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [articleId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center text-gray-400">
        <FileText className="w-16 h-16 mb-4 opacity-50" />
        <h2 className="text-xl font-medium">Article Not Found</h2>
        <Link to="/" className="mt-4 text-blue-400 hover:text-blue-300 flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 overflow-y-auto pb-20">
      {/* Top Navigation */}
      <nav className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur-md border-b border-gray-800/60 px-8 py-4">
        <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-blue-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Datalake Dashboard</span>
        </Link>
      </nav>

      <main className="max-w-4xl mx-auto mt-12 px-6">
        {/* Article Header */}
        <header className="mb-10">
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400 mb-4">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-900 border border-gray-700" title="source">
              <Globe className="w-4 h-4 text-emerald-400" />
              {article.source_domain}
            </span>
            <span className="flex items-center gap-1.5" title="publish date">
              <Clock className="w-4 h-4" />
              {new Date(article.publish_timestamp).toLocaleString()}
            </span>
            {article.author && (
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-900 border border-gray-700/60" title="author">
                <span className="text-gray-500">By</span> <span className="font-medium text-gray-300">{article.author}</span>
              </span>
            )}
            {article.category && (
              <span className="px-3 py-1 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20 capitalize" title="category">
                {article.category}
              </span>
            )}
          </div>

          <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-6 text-gray-100">
            {article.title}
          </h1>

          {/* Tags */}
          {article.extracted_keywords && article.extracted_keywords.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {article.extracted_keywords.slice(0, 5).map((kw, i) => (
                <span key={i} className="text-xs px-2.5 py-1 bg-gray-800 text-gray-300 rounded border border-gray-700">
                  {kw}
                </span>
              ))}
            </div>
          )}
        </header>

        {/* Content Body */}
        <article className="prose prose-invert prose-lg max-w-none text-gray-300 leading-relaxed mb-16">
          {(article.content || article.clean_content) ? (article.content || article.clean_content)!.split('\n\n').map((paragraph, i) => (
            <p key={i} className="mb-6">{paragraph}</p>
          )) : (
            <p className="text-gray-500 italic">No content available.</p>
          )}
        </article>

        {/* Ingested Data Inspector */}
        <div className="mt-16 pt-8 border-t border-gray-800">
          <button 
            onClick={() => setShowRaw(!showRaw)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors mb-4"
          >
            <Code className="w-4 h-4" />
            {showRaw ? "Hide Raw Ingested Data" : "Inspect Raw Ingested Data (Silver Layer)"}
          </button>
          
          {showRaw && (
            <div className="p-6 bg-gray-900 rounded-lg border border-gray-700 max-h-[500px] overflow-y-auto overflow-x-hidden">
              <pre className="text-xs text-green-400 font-mono leading-relaxed whitespace-pre-wrap break-all">
                {JSON.stringify(article, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

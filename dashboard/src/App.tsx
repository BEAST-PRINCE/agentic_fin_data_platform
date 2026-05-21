import { HealthGrid } from './components/HealthGrid';
import { SearchHub } from './components/SearchHub';
import { LiveFeed } from './components/LiveFeed';
import { TrendingRadar } from './components/TrendingRadar';
import { ScraperSidebar } from './components/ScraperSidebar';
import { Database } from 'lucide-react';
import { Routes, Route } from 'react-router-dom';
import { ArticleView } from './components/ArticleView';

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex">
      {/* Sidebar Placeholder for Phase 9 */}
      <ScraperSidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-screen p-8 gap-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-gray-900 via-gray-950 to-black">
        
        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Database className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
                Agentic Data Lakehouse
              </h1>
              <p className="text-sm text-gray-400 mt-1">Operational Intelligence & Semantic Search Hub</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/40 border border-gray-700/50 rounded-full">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-sm font-medium text-emerald-400">System Online</span>
          </div>
        </header>

        {/* Phase 5B Features */}
        <div className="grid grid-cols-12 gap-8">
          
          {/* Top Row: Health & Stats */}
          <div className="col-span-12">
            <HealthGrid />
          </div>

          {/* Center: Search Hub */}
          <div className="col-span-12 lg:col-span-8">
            <SearchHub />
          </div>

          {/* Right: Trending */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-8">
            <TrendingRadar />
          </div>

          {/* Bottom: Live Feed */}
          <div className="col-span-12">
            <LiveFeed />
          </div>

        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />} />
      <Route path="/article/:articleId" element={<ArticleView />} />
    </Routes>
  );
}

export default App;

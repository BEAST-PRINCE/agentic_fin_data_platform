import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ArrowLeft, BrainCircuit, Search, FileText, LineChart, MessageSquare, ArrowDown, FileDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { generatePDF } from '../utils/pdfGenerator';
import { PDFProgressOverlay } from './PDFProgressOverlay';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

const AGENT_PIPELINE = [
  {
    id: 'planner',
    name: 'Planner Agent',
    icon: <BrainCircuit className="w-6 h-6" />,
    description: 'Deconstructs your query, understands the intent, and creates an execution strategy for the rest of the team.',
    color: 'from-fuchsia-500 to-purple-600',
    border: 'border-fuchsia-500/50',
    bg: 'bg-fuchsia-500/20'
  },
  {
    id: 'researcher',
    name: 'Research Agent',
    icon: <Search className="w-6 h-6" />,
    description: 'The data retrieval specialist. Uses MCP tools to search the Vector DB and Lakehouse for evidence.',
    color: 'from-blue-500 to-cyan-500',
    border: 'border-blue-500/50',
    bg: 'bg-blue-500/20'
  },
  {
    id: 'summarizer',
    name: 'Summarization Agent',
    icon: <FileText className="w-6 h-6" />,
    description: 'Compresses large amounts of retrieved data into concise themes and removes redundant information.',
    color: 'from-emerald-500 to-teal-500',
    border: 'border-emerald-500/50',
    bg: 'bg-emerald-500/20'
  },
  {
    id: 'analyst',
    name: 'Analyst Agent',
    icon: <LineChart className="w-6 h-6" />,
    description: 'The reasoning engine. Performs cause-and-effect market analysis and identifies opportunities and risks.',
    color: 'from-amber-500 to-orange-500',
    border: 'border-amber-500/50',
    bg: 'bg-amber-500/20'
  },
  {
    id: 'synthesizer',
    name: 'Synthesizer Agent',
    icon: <MessageSquare className="w-6 h-6" />,
    description: 'Takes all previous findings and structures them into a professional, easy-to-read final report.',
    color: 'from-rose-500 to-pink-600',
    border: 'border-rose-500/50',
    bg: 'bg-rose-500/20'
  }
];

export function MultiAgentDashboard() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'agent', content: 'Hello! We are your specialized Financial Intelligence Team. Ask us complex queries, and our agents will collaborate to research, analyze, and generate a comprehensive report for you.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [hoverY, setHoverY] = useState<number>(0);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [pdfProgress, setPdfProgress] = useState(0);
  const pdfAbortRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    document.title = "Multiagent";
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch('/api/chat/multi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });

      if (!res.ok) throw new Error('Failed to get response');
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'agent', content: data.reply }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'agent', content: 'Sorry, the agent team encountered an error during their analysis.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportPDF = async () => {
    setIsGeneratingPDF(true);
    setPdfProgress(0);
    pdfAbortRef.current = false;

    try {
      await generatePDF({
        messages,
        agentMode: 'Multi-Agent',
        onProgress: setPdfProgress,
        abortRef: pdfAbortRef
      });
    } catch (err) {
      console.error("PDF generation failed", err);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  return (
    <div className="h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-gray-900 via-gray-950 to-black text-gray-100 flex flex-col">
      {isGeneratingPDF && (
        <PDFProgressOverlay 
          progress={pdfProgress} 
          onCancel={() => { pdfAbortRef.current = true; }} 
        />
      )}
      
      {/* Header */}
      <header className="flex items-center gap-4 p-6 border-b border-gray-800/60 bg-gray-950/50 backdrop-blur-md sticky top-0 z-[60]">
        <Link to="/" className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-fuchsia-500/20 flex items-center justify-center border border-fuchsia-500/30 shadow-[0_0_15px_rgba(217,70,239,0.5)]">
            <BrainCircuit className="w-6 h-6 text-fuchsia-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 to-purple-400">
              Multi-Agent Intelligence Team
            </h1>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-xs text-emerald-400 font-medium tracking-wider uppercase">Pipeline Ready</span>
            </div>
          </div>
        </div>

        <div className="ml-auto">
          <button
            onClick={handleExportPDF}
            disabled={isGeneratingPDF || messages.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors text-sm font-medium border border-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileDown className="w-4 h-4" />
            Generate PDF Report
          </button>
        </div>
      </header>

      {/* Main Split Content */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left Panel: Flowchart */}
        <div className="w-1/3 min-w-[320px] hidden lg:flex flex-col border-r border-gray-800/60 bg-gray-900/30 z-20">
          
          {/* Solid Header Block attached to Main Header */}
          <div className="w-full bg-gray-950 border-b border-gray-800 p-4 flex-shrink-0 z-30 shadow-md">
            <h2 className="text-center text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-gray-200 to-gray-400 tracking-widest uppercase">Agent Pipeline</h2>
          </div>
          
          {/* Scrollable Flowchart Area (Scrollbar Hidden) */}
          <div className="flex-1 overflow-y-auto p-8 relative [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            <div className="flex flex-col items-center w-full max-w-[280px] mx-auto pb-16">
              {AGENT_PIPELINE.map((agent, idx) => (
                <div key={agent.id} className="flex flex-col items-center w-full relative">
                  
                  {/* Node */}
                  <div 
                    className={`w-full group relative flex items-center gap-4 p-4 rounded-xl border ${agent.border} ${agent.bg} backdrop-blur-sm shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer ${activeNode === agent.id ? 'z-40' : 'z-10'}`}
                    onMouseEnter={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setHoverY(rect.top + rect.height / 2);
                      setActiveNode(agent.id);
                    }}
                    onMouseLeave={() => setActiveNode(null)}
                  >
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center bg-gradient-to-br ${agent.color} shadow-lg shrink-0`}>
                      <div className="text-white drop-shadow-md">
                        {agent.icon}
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold text-gray-100 text-sm">{agent.name}</h3>
                    </div>
                  </div>

                  {/* Connecting Line with Solid Arrow Head */}
                  {idx < AGENT_PIPELINE.length - 1 && (
                    <div className="flex flex-col items-center my-1 z-0 relative">
                      <div className="w-1 h-10 bg-gray-700/80 rounded-t-full relative">
                        {isLoading && (
                        <div className="absolute top-0 w-full h-full bg-gradient-to-b from-transparent via-fuchsia-500 to-transparent animate-pulse rounded-full opacity-70"></div>
                      )}
                      </div>
                      <div className="w-0 h-0 border-l-[6px] border-r-[6px] border-t-[8px] border-l-transparent border-r-transparent border-t-gray-700/80"></div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Panel: Chat Area */}
        <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-gray-950/20">
          <div className="flex-1 overflow-y-auto p-4 md:p-8">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'agent' && (
                    <div className="w-8 h-8 shrink-0 rounded-full bg-fuchsia-900/40 flex items-center justify-center border border-fuchsia-700/50 mt-1 shadow-[0_0_10px_rgba(217,70,239,0.2)]">
                      <BrainCircuit className="w-5 h-5 text-fuchsia-400" />
                    </div>
                  )}
                  
                  <div className={`max-w-[80%] rounded-2xl p-4 shadow-lg ${
                    msg.role === 'user' 
                      ? 'bg-emerald-600/20 border border-emerald-500/30 text-emerald-50 rounded-tr-sm shadow-emerald-900/20' 
                      : 'bg-gray-800/60 border border-gray-700/50 text-gray-200 rounded-tl-sm backdrop-blur-md'
                  }`}>
                    <div className="prose prose-invert max-w-none">
                      <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{msg.content}</pre>
                    </div>
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-8 h-8 shrink-0 rounded-full bg-emerald-900/40 flex items-center justify-center border border-emerald-700/50 mt-1">
                      <User className="w-5 h-5 text-emerald-400" />
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-4 justify-start">
                  <div className="w-8 h-8 shrink-0 rounded-full bg-fuchsia-900/40 flex items-center justify-center border border-fuchsia-700/50 mt-1">
                    <BrainCircuit className="w-5 h-5 text-fuchsia-400" />
                  </div>
                  <div className="bg-gray-800/60 border border-gray-700/50 rounded-2xl rounded-tl-sm p-4 flex flex-col gap-3 shadow-lg backdrop-blur-md w-64">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-fuchsia-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-fuchsia-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      <span className="text-xs text-fuchsia-400 ml-3 font-medium tracking-wide uppercase">Pipeline Running</span>
                    </div>
                    <div className="text-[10px] text-gray-400 uppercase tracking-wider">
                      Agents are actively collaborating...
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 md:p-6 border-t border-gray-800/60 bg-gray-950/90 backdrop-blur-xl">
            <div className="max-w-4xl mx-auto relative flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask the team to analyze a financial topic..."
                className="w-full bg-gray-900/50 border border-gray-700 rounded-xl py-3 px-4 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent resize-none h-[52px] max-h-[200px] transition-all shadow-inner"
                rows={1}
                style={{
                  height: '52px',
                  minHeight: '52px'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = '52px';
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
                }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`h-[52px] px-6 rounded-xl flex items-center justify-center transition-all ${
                  !input.trim() || isLoading 
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed' 
                    : 'bg-fuchsia-600 hover:bg-fuchsia-500 text-white shadow-[0_0_15px_rgba(192,38,211,0.4)]'
                }`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Global Viewport-Relative Tooltip (Breaks out of all containers) */}
      {activeNode && AGENT_PIPELINE.map(agent => agent.id === activeNode && (
        <div 
          key={`tooltip-${agent.id}`}
          className={`fixed z-[200] w-[320px] p-5 rounded-xl bg-gray-950/95 backdrop-blur-xl border ${agent.border} shadow-[0_0_40px_rgba(0,0,0,0.8)] transition-all duration-150 pointer-events-none`}
          style={{ 
            top: `${hoverY}px`, 
            left: 'calc(33.333333% + 20px)', 
            transform: 'translateY(-50%)'
          }}
        >
          <div className="!border-0"> 
            <h4 className="font-bold text-gray-100 mb-2">{agent.name}</h4>
            <p className="text-sm text-gray-300 leading-relaxed">{agent.description}</p>
            {/* Pointer arrow */}
            <div 
              className={`absolute top-1/2 -left-2 -translate-y-1/2 w-4 h-4 bg-gray-950 border-l border-b ${agent.border} rotate-45`}
            ></div>
          </div>
        </div>
      ))}
    </div>
  );
}

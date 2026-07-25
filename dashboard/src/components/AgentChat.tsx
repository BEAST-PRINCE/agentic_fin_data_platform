import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ArrowLeft, FileDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { generatePDF } from '../utils/pdfGenerator';
import { PDFProgressOverlay } from './PDFProgressOverlay';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'agent', content: 'Hello! I am your Agentic Datalake Assistant. I have access to your semantic search index and daily trends. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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
    document.title = "Intelligent-agent";
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });

      if (!res.ok) throw new Error('Failed to get response');
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'agent', content: data.reply }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'agent', content: 'Sorry, I encountered an error communicating with the datalake tools.' }]);
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
        agentMode: 'Single Agent',
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
      <header className="flex items-center gap-4 p-6 border-b border-gray-800/60 bg-gray-950/50 backdrop-blur-md sticky top-0 z-10">
        <Link to="/" className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            <Bot className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              Intelligence Agent
            </h1>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></span>
              System Online
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

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'agent' && (
                <div className="w-8 h-8 shrink-0 rounded-full bg-blue-900/40 flex items-center justify-center border border-blue-700/50 mt-1">
                  <Bot className="w-5 h-5 text-blue-400" />
                </div>
              )}
              
              <div className={`max-w-[80%] rounded-2xl p-4 shadow-lg ${
                msg.role === 'user' 
                  ? 'bg-emerald-600/20 border border-emerald-500/30 text-emerald-50 rounded-tr-sm shadow-emerald-900/20' 
                  : 'bg-gray-800/40 border border-gray-700/50 text-gray-200 rounded-tl-sm backdrop-blur-sm'
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
              <div className="w-8 h-8 shrink-0 rounded-full bg-blue-900/40 flex items-center justify-center border border-blue-700/50 mt-1">
                <Bot className="w-5 h-5 text-blue-400" />
              </div>
              <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl rounded-tl-sm p-4 flex items-center gap-2 shadow-lg backdrop-blur-sm">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="text-xs text-blue-400 ml-3 font-medium tracking-wide uppercase">Searching Datalake...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="p-4 md:p-6 border-t border-gray-800/60 bg-gray-950/80 backdrop-blur-xl">
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
            placeholder="Ask me anything about the datalake..."
            className="w-full bg-gray-900/50 border border-gray-700 rounded-xl py-3 px-4 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none h-[52px] max-h-[200px] transition-all shadow-inner"
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
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </footer>
    </div>
  );
}

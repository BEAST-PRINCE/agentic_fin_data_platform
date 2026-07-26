import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, Clock, Sparkles, Code2 } from 'lucide-react';

export interface WorkflowStep {
  agent: string;
  status: string;
  summary: string;
  details?: any;
  execution_time_ms?: number;
}

interface AgentWorkflowAccordionProps {
  steps?: WorkflowStep[];
}

export const AgentWorkflowAccordion: React.FC<AgentWorkflowAccordionProps> = ({ steps }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedDetailIdx, setExpandedDetailIdx] = useState<number | null>(null);

  if (!steps || steps.length === 0) return null;

  const totalTimeMs = steps.reduce((acc, curr) => acc + (curr.execution_time_ms || 0), 0);

  const toggleDetail = (idx: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedDetailIdx(prev => (prev === idx ? null : idx));
  };

  return (
    <div className="mt-4 border-t border-gray-700/40 pt-3">
      {/* Header Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-3 py-2 text-xs font-medium text-purple-300 hover:text-purple-200 bg-purple-950/30 hover:bg-purple-900/40 border border-purple-800/40 rounded-xl transition-all shadow-sm group"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-purple-400 group-hover:rotate-12 transition-transform" />
          <span>Agent Workflow</span>
          <span className="bg-purple-900/60 text-purple-300 text-[10px] px-2 py-0.5 rounded-full border border-purple-700/50">
            {steps.length} Agents
          </span>
        </div>

        <div className="flex items-center gap-3">
          {totalTimeMs > 0 && (
            <div className="flex items-center gap-1 text-[11px] text-gray-400">
              <Clock className="w-3 h-3 text-purple-400" />
              <span>{totalTimeMs} ms</span>
            </div>
          )}
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-purple-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-purple-400" />
          )}
        </div>
      </button>

      {/* Accordion Body */}
      {isOpen && (
        <div className="mt-3 space-y-2 pl-1 animate-in fade-in-50 duration-200">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="p-2.5 bg-gray-900/60 border border-gray-800 rounded-xl text-xs flex flex-col gap-1.5 transition-all hover:border-gray-700/80"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-gray-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{step.agent}</span>
                </div>

                <div className="flex items-center gap-2">
                  {step.execution_time_ms && (
                    <span className="text-[10px] text-gray-500 font-mono">
                      {step.execution_time_ms} ms
                    </span>
                  )}
                  {step.details && (
                    <button
                      onClick={(e) => toggleDetail(idx, e)}
                      className="flex items-center gap-1 text-[10px] text-purple-400 hover:text-purple-300 bg-purple-950/40 hover:bg-purple-900/60 px-1.5 py-0.5 rounded border border-purple-800/40 transition-colors"
                    >
                      <Code2 className="w-3 h-3" />
                      {expandedDetailIdx === idx ? 'Hide JSON' : 'View JSON'}
                    </button>
                  )}
                </div>
              </div>

              <div className="text-gray-300 text-[11px] leading-relaxed pl-5">
                {step.summary}
              </div>

              {/* JSON Detail Drawer */}
              {expandedDetailIdx === idx && step.details && (
                <div className="mt-2 ml-5 p-2 bg-gray-950 rounded-lg border border-gray-800 text-[10px] font-mono text-emerald-400 overflow-x-auto max-h-48 scrollbar-thin">
                  <pre className="whitespace-pre-wrap leading-tight">
                    {typeof step.details === 'string'
                      ? step.details
                      : JSON.stringify(step.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

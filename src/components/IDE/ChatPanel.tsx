import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MessageSquare, Code, FileText, Sparkles } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  files?: string[];
  codeBlocks?: Array<{
    language: string;
    code: string;
    filename?: string;
  }>;
}

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  onCreateFile?: (filename: string, content: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSendMessage,
  isLoading,
  onCreateFile
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const renderCodeBlock = (codeBlock: any, index: number) => (
    <div key={index} className="mt-3 bg-slate-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 text-slate-300 text-sm">
        <div className="flex items-center space-x-2">
          <Code className="h-4 w-4" />
          <span>{codeBlock.filename || codeBlock.language}</span>
        </div>
        {onCreateFile && codeBlock.filename && (
          <button
            onClick={() => onCreateFile(codeBlock.filename, codeBlock.code)}
            className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
          >
            Create File
          </button>
        )}
      </div>
      <pre className="p-4 text-sm text-slate-100 overflow-x-auto">
        <code>{codeBlock.code}</code>
      </pre>
    </div>
  );

  const suggestedPrompts = [
    "Create a modern landing page for a tech startup",
    "Build an e-commerce website with product listings",
    "Make a portfolio website for a designer",
    "Create a restaurant website with menu and booking",
    "Build a blog website with multiple pages",
    "Make a dashboard with charts and analytics",
    "Create a social media app interface",
    "Build a real estate website with property listings"
  ];

  return (
    <div className="flex flex-col h-full bg-white border-r border-slate-200">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-900">AI Assistant</h2>
            <p className="text-sm text-slate-600">Build anything with AI</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="space-y-4">
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                Start Building
              </h3>
              <p className="text-slate-600 mb-6">
                Describe what you want to build and I'll create it for you
              </p>
            </div>
            
            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-700 mb-3">Try these prompts:</p>
              {suggestedPrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => setInput(prompt)}
                  className="w-full text-left p-3 bg-slate-50 hover:bg-slate-100 rounded-lg text-sm text-slate-700 transition-colors border border-slate-200"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="space-y-2">
              <div
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] p-3 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                  
                  {message.codeBlocks?.map((codeBlock, index) => 
                    renderCodeBlock(codeBlock, index)
                  )}
                  
                  {message.files && message.files.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-300/30">
                      <p className="text-xs opacity-75 mb-2">Files created/modified:</p>
                      <div className="flex flex-wrap gap-1">
                        {message.files.map((file, index) => (
                          <span
                            key={index}
                            className="text-xs px-2 py-1 bg-black/10 rounded-full flex items-center space-x-1"
                          >
                            <FileText className="h-3 w-3" />
                            <span>{file}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 p-3 rounded-lg flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span className="text-slate-600 text-sm">Generating code...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-200">
        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe what you want to build..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-100 disabled:text-slate-400 text-sm"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center space-x-2"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
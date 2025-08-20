import React, { useState, useEffect } from 'react';
import { ChatPanel } from './ChatPanel';
import { FileExplorer } from './FileExplorer';
import { CodeEditor } from './CodeEditor';
import { PreviewPanel } from './PreviewPanel';
import { Terminal } from './Terminal';
import { TerminalIcon, Layout, PanelLeftClose, PanelLeftOpen, Zap } from 'lucide-react';
import { API_BASE_URL } from '../../config/api';

interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  path: string;
  children?: FileNode[];
  content?: string;
  language?: string;
}

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

export const BoltIDE: React.FC = () => {
  const [files, setFiles] = useState<FileNode[]>([
    {
      id: '1',
      name: 'src',
      type: 'folder',
      path: 'src',
      children: [
        {
          id: '2',
          name: 'App.tsx',
          type: 'file',
          path: 'src/App.tsx',
          content: `import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Bolt IDE
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Ask AI to create any website and watch it come to life!
        </p>
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
          <p className="text-sm text-gray-500">
            Try prompts like:
          </p>
          <ul className="text-sm text-gray-700 mt-2 space-y-1">
            <li>• "Create a modern landing page"</li>
            <li>• "Build an e-commerce website"</li>
            <li>• "Make a portfolio site"</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;`,
          language: 'typescript'
        }
      ]
    }
  ]);

  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showTerminal, setShowTerminal] = useState(false);
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

  // Set initial selected file
  useEffect(() => {
    const appFile = findFileByPath(files, 'src/App.tsx');
    if (appFile && !selectedFile) {
      setSelectedFile(appFile);
    }
  }, [files, selectedFile]);

  const findFileByPath = (fileNodes: FileNode[], targetPath: string): FileNode | null => {
    for (const node of fileNodes) {
      if (node.path === targetPath) {
        return node;
      }
      if (node.children) {
        const found = findFileByPath(node.children, targetPath);
        if (found) return found;
      }
    }
    return null;
  };

  const convertApiFilesToFileNodes = (apiFiles: Array<{path: string, content: string}>): FileNode[] => {
    const fileMap = new Map<string, FileNode>();
    const rootNodes: FileNode[] = [];

    // Create all file nodes first
    apiFiles.forEach((file, index) => {
      const parts = file.path.split('/');
      const fileName = parts[parts.length - 1];
      const fileNode: FileNode = {
        id: `file-${index}`,
        name: fileName,
        type: 'file',
        path: file.path,
        content: file.content,
        language: fileName.split('.').pop() || 'text'
      };
      fileMap.set(file.path, fileNode);
    });

    // Create folder structure
    const folderMap = new Map<string, FileNode>();
    
    apiFiles.forEach((file) => {
      const parts = file.path.split('/');
      let currentPath = '';
      
      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        const parentPath = currentPath;
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        
        if (!folderMap.has(currentPath)) {
          const folderNode: FileNode = {
            id: `folder-${currentPath}`,
            name: part,
            type: 'folder',
            path: currentPath,
            children: []
          };
          folderMap.set(currentPath, folderNode);
          
          if (parentPath) {
            const parentFolder = folderMap.get(parentPath);
            if (parentFolder && parentFolder.children) {
              parentFolder.children.push(folderNode);
            }
          } else {
            rootNodes.push(folderNode);
          }
        }
      }
      
      // Add file to its parent folder
      const fileNode = fileMap.get(file.path);
      if (fileNode) {
        const parentPath = parts.slice(0, -1).join('/');
        if (parentPath) {
          const parentFolder = folderMap.get(parentPath);
          if (parentFolder && parentFolder.children) {
            parentFolder.children.push(fileNode);
          }
        } else {
          rootNodes.push(fileNode);
        }
      }
    });

    return rootNodes;
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-website`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.files_written && result.files_written.length > 0) {
        // Reload the file structure by reading the written files
        await refreshFileStructure();

        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `✅ Successfully generated your website!\n\n📁 Created ${result.total_files} files:\n${result.files_written.map((file: string) => `• ${file}`).join('\n')}\n\nYour website is now live in the preview panel!`,
          timestamp: new Date(),
          files: result.files_written
        };

        setMessages(prev => [...prev, aiResponse]);
      } else {
        throw new Error(result.errors?.join(', ') || 'Failed to generate website');
      }
    } catch (error) {
      console.error('Error generating website:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `❌ Sorry, I encountered an error generating your website: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease try again with a different prompt.`,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshFileStructure = async () => {
    try {
      // In a real implementation, you might want to read the actual file system
      // For now, we'll make a simple request to get the current state
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        // Force a page reload to pick up new files
        // In production, you'd implement a proper file system watcher
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } catch (error) {
      console.error('Error refreshing file structure:', error);
    }
  };

  const handleFileSelect = (file: FileNode) => {
    if (file.type === 'file') {
      setSelectedFile(file);
    }
  };

  const handleFileSave = (path: string, content: string) => {
    setFiles(prevFiles => {
      const updateFileContent = (nodes: FileNode[]): FileNode[] => {
        return nodes.map(node => {
          if (node.path === path) {
            return { ...node, content };
          }
          if (node.children) {
            return { ...node, children: updateFileContent(node.children) };
          }
          return node;
        });
      };
      return updateFileContent(prevFiles);
    });

    if (selectedFile?.path === path) {
      setSelectedFile(prev => prev ? { ...prev, content } : null);
    }
  };

  const handleCreateFile = (filename: string, content: string) => {
    const newFile: FileNode = {
      id: Date.now().toString(),
      name: filename.split('/').pop() || filename,
      type: 'file',
      path: filename,
      content,
      language: filename.split('.').pop() || 'text'
    };

    setFiles(prevFiles => {
      const addToSrc = (nodes: FileNode[]): FileNode[] => {
        return nodes.map(node => {
          if (node.path === 'src' && node.children) {
            return {
              ...node,
              children: [...node.children, newFile]
            };
          }
          if (node.children) {
            return { ...node, children: addToSrc(node.children) };
          }
          return node;
        });
      };
      return addToSrc(prevFiles);
    });

    setSelectedFile(newFile);
  };

  const handleFileCreate = (path: string, type: 'file' | 'folder') => {
    console.log('Create', type, 'at', path);
  };

  const handleFileDelete = (path: string) => {
    setFiles(prevFiles => {
      const removeFile = (nodes: FileNode[]): FileNode[] => {
        return nodes.filter(node => {
          if (node.path === path) {
            return false;
          }
          if (node.children) {
            node.children = removeFile(node.children);
          }
          return true;
        });
      };
      return removeFile(prevFiles);
    });

    if (selectedFile?.path === path) {
      setSelectedFile(null);
    }
  };

  const handleFileRename = (oldPath: string, newPath: string) => {
    console.log('Rename', oldPath, 'to', newPath);
  };

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      {/* Top Bar */}
      <div className="h-12 bg-slate-900 text-white flex items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-blue-400" />
            <span className="font-semibold">Bolt IDE</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
            title="Toggle left panel"
          >
            {leftPanelCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
          
          <button
            onClick={() => setShowTerminal(!showTerminal)}
            className={`p-1.5 rounded transition-colors ${
              showTerminal 
                ? 'text-blue-400 bg-slate-700' 
                : 'text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
            title="Toggle terminal"
          >
            <TerminalIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat */}
        {!leftPanelCollapsed && (
          <div className="w-80 flex-shrink-0">
            <ChatPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              onCreateFile={handleCreateFile}
            />
          </div>
        )}

        {/* Center Panel - Editor */}
        <div className="flex-1 flex flex-col">
          <div className={`flex-1 ${showTerminal ? 'h-1/2' : ''}`}>
            <CodeEditor
              file={selectedFile}
              onSave={handleFileSave}
            />
          </div>
          
          {/* Terminal */}
          <Terminal
            isVisible={showTerminal}
            onToggle={() => setShowTerminal(!showTerminal)}
          />
        </div>

        {/* Right Panel - File Explorer & Preview */}
        {!rightPanelCollapsed && (
          <div className="w-80 flex-shrink-0 flex flex-col">
            {/* File Explorer */}
            <div className="h-1/2 border-b border-slate-200">
              <FileExplorer
                files={files}
                selectedFile={selectedFile?.path}
                onFileSelect={handleFileSelect}
                onFileCreate={handleFileCreate}
                onFileDelete={handleFileDelete}
                onFileRename={handleFileRename}
              />
            </div>
            
            {/* Preview */}
            <div className="h-1/2">
              <PreviewPanel />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { motion } from 'framer-motion';
import { Plus, Edit2, Settings, User, Database, Code, Search, Brain, Bot, FileText } from 'lucide-react';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

// Sample agent data
const sampleAgents = [
  {
    id: '1',
    name: 'Query Analyzer',
    description: 'Analyzes and extracts key entities from user questions',
    icon: <Search className="h-8 w-8 mb-2" />,
    type: 'nlp',
    model_name: 'gpt-4',
    temperature: 0.2,
    system_prompt: 'You are a query understanding specialist. Your task is to analyze user queries, identify their intent, and extract key entities. Provide a structured output of the intent and entities found.',
    color: 'bg-[#8A2BE2]',
  },
  {
    id: '2',
    name: 'Data Explorer',
    description: 'Explores and summarizes data from various sources',
    icon: <Database className="h-8 w-8 mb-2" />,
    type: 'retrieval',
    model_name: 'gpt-4',
    temperature: 0.3,
    system_prompt: 'You are a data exploration expert. Your role is to query, analyze, and synthesize information from various data sources. Provide clear summaries and extract relevant insights.',
    color: 'bg-[#03DAC6]',
  },
  {
    id: '3',
    name: 'Code Assistant',
    description: 'Writes and reviews code snippets',
    icon: <Code className="h-8 w-8 mb-2" />,
    type: 'coding',
    model_name: 'gpt-4',
    temperature: 0.1,
    system_prompt: 'You are a coding assistant specialized in writing clean, efficient code. Ensure proper error handling, use best practices, and provide explanations for complex implementations.',
    color: 'bg-[#FF5722]',
  },
  {
    id: '4',
    name: 'Planning Agent',
    description: 'Creates execution plans for complex tasks',
    icon: <Brain className="h-8 w-8 mb-2" />,
    type: 'planning',
    model_name: 'gpt-4',
    temperature: 0.4,
    system_prompt: 'You are a planning specialist. Your task is to break down complex objectives into clear, actionable steps. Create sequential plans that are easy to follow and execute.',
    color: 'bg-[#00B0FF]',
  },
  {
    id: '5',
    name: 'Conversation Bot',
    description: 'Engages in natural, helpful dialogue',
    icon: <Bot className="h-8 w-8 mb-2" />,
    type: 'conversation',
    model_name: 'gpt-4',
    temperature: 0.7,
    system_prompt: 'You are a helpful, friendly conversation assistant. Engage with users in a natural way, understand context, and provide relevant, accurate information while maintaining a personable tone.',
    color: 'bg-[#FFB300]',
  },
  {
    id: '6',
    name: 'Document Processor',
    description: 'Extracts and summarizes information from documents',
    icon: <FileText className="h-8 w-8 mb-2" />,
    type: 'document',
    model_name: 'gpt-4',
    temperature: 0.3,
    system_prompt: 'You are a document processing specialist. Your job is to extract key information from various document types, create accurate summaries, and identify important entities and relationships.',
    color: 'bg-[#00E676]',
  },
];

export default function AgentRepository() {
  const [agents, setAgents] = useState(sampleAgents);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<any>(null);

  const handleEditAgent = (agent: any) => {
    setCurrentAgent(agent);
    setIsDialogOpen(true);
  };

  const handleSaveAgent = (e: React.FormEvent) => {
    e.preventDefault();
    setIsDialogOpen(false);
    // In a real app, we would save the agent to the backend
    console.log('Saving agent:', currentAgent);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-heading font-semibold">Agent Repository</h2>
        <Button className="bg-primary hover:bg-opacity-80 flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create New Agent
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card className="bg-background-card shadow-card border-gray-800 h-full flex flex-col">
              <CardHeader className={`py-4 px-6 ${agent.color} bg-opacity-10 border-b border-gray-800`}>
                <div className="flex justify-between items-start">
                  <div className="flex flex-col items-center justify-center">
                    <div className={`${agent.color} p-2 rounded-lg text-white`}>
                      {agent.icon}
                    </div>
                  </div>
                  <CardTitle className="text-lg font-heading">{agent.name}</CardTitle>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="text-gray-400 hover:text-gray-100"
                    onClick={() => handleEditAgent(agent)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-4 flex-grow">
                <p className="text-sm text-gray-400">{agent.description}</p>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Type:</span>
                    <span className="text-xs font-medium">{agent.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Model:</span>
                    <span className="text-xs font-medium">{agent.model_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Temperature:</span>
                    <span className="text-xs font-medium">{agent.temperature}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="px-6 py-4 border-t border-gray-800 bg-background-dark">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full flex items-center justify-center gap-2"
                >
                  <Settings className="h-3 w-3" />
                  Configure
                </Button>
              </CardFooter>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Edit agent dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-background-card border-gray-800 text-foreground max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Agent Configuration</DialogTitle>
            <DialogDescription>
              Modify the agent's settings and system prompt to customize its behavior.
            </DialogDescription>
          </DialogHeader>
          
          {currentAgent && (
            <form onSubmit={handleSaveAgent} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="agent-name">Agent Name</Label>
                  <Input 
                    id="agent-name" 
                    value={currentAgent.name}
                    onChange={(e) => setCurrentAgent({...currentAgent, name: e.target.value})}
                    className="bg-background-dark"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="agent-type">Agent Type</Label>
                  <Select 
                    value={currentAgent.type}
                    onValueChange={(value) => setCurrentAgent({...currentAgent, type: value})}
                  >
                    <SelectTrigger id="agent-type" className="bg-background-dark">
                      <SelectValue placeholder="Select agent type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nlp">NLP</SelectItem>
                      <SelectItem value="retrieval">Retrieval</SelectItem>
                      <SelectItem value="coding">Coding</SelectItem>
                      <SelectItem value="planning">Planning</SelectItem>
                      <SelectItem value="conversation">Conversation</SelectItem>
                      <SelectItem value="document">Document</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="model-name">Model</Label>
                  <Select 
                    value={currentAgent.model_name}
                    onValueChange={(value) => setCurrentAgent({...currentAgent, model_name: value})}
                  >
                    <SelectTrigger id="model-name" className="bg-background-dark">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4">GPT-4</SelectItem>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      <SelectItem value="claude-2">Claude 2</SelectItem>
                      <SelectItem value="llama-2">Llama 2</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperature</Label>
                  <div className="flex items-center gap-4">
                    <Input
                      id="temperature"
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={currentAgent.temperature}
                      onChange={(e) => setCurrentAgent({...currentAgent, temperature: parseFloat(e.target.value)})}
                      className="flex-grow"
                    />
                    <span className="w-10 text-center">{currentAgent.temperature}</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="system-prompt">System Prompt</Label>
                <Textarea 
                  id="system-prompt"
                  value={currentAgent.system_prompt}
                  onChange={(e) => setCurrentAgent({...currentAgent, system_prompt: e.target.value})}
                  rows={6}
                  className="bg-background-dark resize-none"
                />
                <p className="text-xs text-gray-400">
                  The system prompt defines the agent's behavior, capabilities, and constraints.
                </p>
              </div>
              
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-[#8A2BE2] hover:bg-opacity-80">
                  Save Changes
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
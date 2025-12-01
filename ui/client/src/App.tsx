import { ProjectProvider } from '@/contexts/ProjectContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { NotificationProvider } from '@/contexts/NotificationContext';
import { SharedProvider } from '@/contexts/SharedContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { Route, Switch } from "wouter";
import { useEffect } from "react";  
import Dashboard from "@/pages/Dashboard";
import Configuration from "@/pages/Configuration";
import JiraIntegration from "@/pages/JiraIntegration";
import AgenticAI from "@/pages/AgenticAI";
import AgentRepository from "@/pages/AgentRepository";
import AgenticChats from "@/pages/AgenticChats";
import NotFound from "@/pages/not-found";
import DocumentsPage from "./features/docs/DocumentsPage";
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import SlackIntegration from "./features/slack/SlackIntegration";
import SlackAddSourcePage from "./features/slack/SlackAddSourcePage";
import GuidesPage from "./components/guides/GuidesPage";

function App(): any {
  useEffect(() => {
    document.title = "UnifAI";
    fetch('/api/config').then(r => r.json());
  }, []);

  return (
    <ThemeProvider>
      <AuthProvider>
        <NotificationProvider>
          <SharedProvider>
            <ProjectProvider>
              <ProtectedRoute>
                <Switch>
                  <Route path="/" component={AgenticAI} />
                  <Route path="/jira" component={JiraIntegration} />
                  <Route path="/slack" component={SlackIntegration} />
                  <Route path="/documents" component={DocumentsPage} />
                  <Route path="/inventory" component={AgentRepository} />
                  <Route path="/agentic-ai" component={AgenticAI} />
                  <Route path="/agentic-chats" component={AgenticChats} />
                  <Route path="/slack/add-source" component={SlackAddSourcePage} />
                  <Route path="/configuration" component={Configuration} />
                  <Route path="/guides" component={GuidesPage} />
                  <Route component={NotFound} />
                </Switch>
              </ProtectedRoute>
            </ProjectProvider>
          </SharedProvider>
        </NotificationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
              

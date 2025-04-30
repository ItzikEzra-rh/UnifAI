import { Route, Switch } from "wouter";
import Dashboard from "@/pages/Dashboard";
import Configuration from "@/pages/Configuration";
import JiraIntegration from "@/pages/JiraIntegration";
import SlackIntegration from "@/pages/SlackIntegration";
import Documents from "@/pages/Documents";
import NotFound from "@/pages/not-found";
import { useEffect } from "react";
import { ProjectProvider } from '@/contexts/ProjectContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

function App() {
  // Set document title
  useEffect(() => {
    document.title = "DataFlow Pro - Modern Pipeline Management";
  }, []);

  return (
    <ThemeProvider>
      <ProjectProvider>
        <Switch>
          <Route path="/" component={Dashboard} />
          <Route path="/configuration" component={Configuration} />
          <Route path="/jira" component={JiraIntegration} />
          <Route path="/slack" component={SlackIntegration} />
          <Route path="/documents" component={Documents} />
          <Route component={NotFound} />
        </Switch>
      </ProjectProvider>
    </ThemeProvider>
  );
}

export default App;

import { useState, useCallback } from 'react';
import { 
  Template, 
  TemplateInstantiationResponse,
  InstantiationStatusResponse,
  InstantiationStatus,
  TemplateCategory
} from '../types/templates';
import { 
  fetchTemplates as fetchTemplatesApi,
  fetchTemplateById as fetchTemplateByIdApi,
  instantiateTemplate as instantiateTemplateApi,
  getInstantiationStatus
} from '../api/templates';
import { useToast } from './use-toast';

interface UseTemplatesReturn {
  templates: Template[];
  selectedTemplate: Template | null;
  isLoading: boolean;
  error: string | null;
  instantiationStatus: InstantiationStatus;
  instantiationResult: TemplateInstantiationResponse | null;
  fetchTemplates: () => Promise<Template[] | null>;
  fetchTemplateById: (id: string) => Promise<Template | null>;
  instantiateTemplate: (templateId: string, inputs: Record<string, any>) => Promise<TemplateInstantiationResponse | null>;
  checkInstantiationStatus: (instanceId: string) => Promise<InstantiationStatusResponse | null>;
  resetInstantiation: () => void;
  getCategories: () => TemplateCategory[];
  filterTemplates: (searchQuery?: string, category?: string | null) => Template[];
  setSelectedTemplate: (template: Template | null) => void;
}

const MOCK_TEMPLATES: Template[] = [
  {
    id: 'weekly-report-agent',
    name: 'Weekly Activity User Report',
    description: 'Automatically generate comprehensive weekly activity reports from GitHub, Jira, and Slack data. This template creates a multi-agent workflow that aggregates user activities across platforms and generates summarized reports.',
    category: 'Reports',
    version: '1.0.0',
    icon: 'FileText',
    estimated_setup_time: '5 minutes',
    tags: ['reporting', 'automation', 'productivity'],
    output_capabilities: ['Weekly PDF Reports', 'Email Notifications', 'Dashboard Integration'],
    fields: [
      {
        key: 'github_token',
        label: 'GitHub Token',
        type: 'secret',
        required: true,
        description: 'Personal access token with repo read permissions',
        ui_hints: { masked: true, placeholder: 'ghp_xxxxxxxxxxxx' }
      },
      {
        key: 'jira_token',
        label: 'Jira API Token',
        type: 'secret',
        required: true,
        description: 'Jira API token for accessing project data',
        ui_hints: { masked: true }
      },
      {
        key: 'jira_projects',
        label: 'Jira Projects',
        type: 'string[]',
        required: true,
        description: 'List of Jira project keys to include in the report',
        ui_hints: { tagInput: true, placeholder: 'Add project key...' }
      },
      {
        key: 'github_repos',
        label: 'GitHub Repositories',
        type: 'string[]',
        required: true,
        description: 'List of GitHub repositories to track (format: owner/repo)',
        ui_hints: { tagInput: true, placeholder: 'owner/repo' }
      },
      {
        key: 'user_emails',
        label: 'User Emails',
        type: 'string[]',
        required: true,
        description: 'Email addresses of users to include in the report',
        ui_hints: { tagInput: true, placeholder: 'user@example.com' }
      },
      {
        key: 'report_frequency',
        label: 'Report Frequency',
        type: 'enum',
        required: false,
        default: 'weekly',
        options: ['daily', 'weekly', 'biweekly', 'monthly'],
        description: 'How often to generate the report'
      }
    ]
  },
  {
    id: 'support-bot-agent',
    name: 'Customer Support Bot',
    description: 'Deploy an intelligent customer support chatbot powered by LLMs with retrieval-augmented generation. Connects to your knowledge base and provides accurate, context-aware responses.',
    category: 'Chatbots',
    version: '1.0.0',
    icon: 'MessageSquare',
    estimated_setup_time: '10 minutes',
    tags: ['customer-support', 'chatbot', 'rag'],
    output_capabilities: ['24/7 Support', 'Multi-channel Integration', 'Analytics Dashboard'],
    fields: [
      {
        key: 'knowledge_base_url',
        label: 'Knowledge Base URL',
        type: 'string',
        required: true,
        description: 'URL to your documentation or knowledge base',
        validation: { regex: '^https?://' },
        ui_hints: { placeholder: 'https://docs.yourcompany.com' }
      },
      {
        key: 'openai_api_key',
        label: 'OpenAI API Key',
        type: 'secret',
        required: true,
        description: 'API key for OpenAI GPT models',
        ui_hints: { masked: true }
      },
      {
        key: 'bot_name',
        label: 'Bot Name',
        type: 'string',
        required: false,
        default: 'Support Assistant',
        description: 'Display name for the support bot'
      },
      {
        key: 'welcome_message',
        label: 'Welcome Message',
        type: 'string',
        required: false,
        default: 'Hello! How can I help you today?',
        description: 'Initial greeting message for users',
        ui_hints: { rows: 3 }
      },
      {
        key: 'escalation_enabled',
        label: 'Enable Human Escalation',
        type: 'boolean',
        required: false,
        default: true,
        description: 'Allow users to request human support'
      }
    ]
  },
  {
    id: 'data-pipeline-agent',
    name: 'Automated Data Pipeline',
    description: 'Create an intelligent data pipeline that monitors data sources, performs transformations, and loads data into your warehouse with anomaly detection and quality checks.',
    category: 'Data Engineering',
    version: '1.0.0',
    icon: 'Database',
    estimated_setup_time: '15 minutes',
    tags: ['etl', 'data-pipeline', 'automation'],
    output_capabilities: ['Automated ETL', 'Data Quality Monitoring', 'Anomaly Alerts'],
    fields: [
      {
        key: 'source_connection',
        label: 'Source Database Connection',
        type: 'secret',
        required: true,
        description: 'Connection string for source database',
        ui_hints: { masked: true, placeholder: 'postgresql://user:pass@host:5432/db' }
      },
      {
        key: 'target_connection',
        label: 'Target Warehouse Connection',
        type: 'secret',
        required: true,
        description: 'Connection string for target data warehouse',
        ui_hints: { masked: true }
      },
      {
        key: 'tables',
        label: 'Tables to Sync',
        type: 'string[]',
        required: true,
        description: 'List of tables to include in the pipeline',
        ui_hints: { tagInput: true }
      },
      {
        key: 'sync_frequency',
        label: 'Sync Frequency',
        type: 'enum',
        required: false,
        default: 'hourly',
        options: ['realtime', 'hourly', 'daily', 'weekly'],
        description: 'How often to sync data'
      },
      {
        key: 'enable_quality_checks',
        label: 'Enable Quality Checks',
        type: 'boolean',
        required: false,
        default: true,
        description: 'Run data quality validation on each sync'
      }
    ]
  },
  {
    id: 'code-review-agent',
    name: 'AI Code Review Assistant',
    description: 'Automated code review agent that analyzes pull requests, suggests improvements, checks for security vulnerabilities, and ensures code quality standards.',
    category: 'Development',
    version: '1.0.0',
    icon: 'GitBranch',
    estimated_setup_time: '8 minutes',
    tags: ['code-review', 'development', 'security'],
    output_capabilities: ['PR Comments', 'Security Scanning', 'Style Enforcement'],
    fields: [
      {
        key: 'github_app_key',
        label: 'GitHub App Private Key',
        type: 'secret',
        required: true,
        description: 'Private key for your GitHub App',
        ui_hints: { masked: true, rows: 5 }
      },
      {
        key: 'github_app_id',
        label: 'GitHub App ID',
        type: 'string',
        required: true,
        description: 'Your GitHub App installation ID'
      },
      {
        key: 'repos_to_monitor',
        label: 'Repositories to Monitor',
        type: 'string[]',
        required: true,
        description: 'List of repositories to enable code review on',
        ui_hints: { tagInput: true }
      },
      {
        key: 'review_style',
        label: 'Review Style',
        type: 'enum',
        required: false,
        default: 'balanced',
        options: ['lenient', 'balanced', 'strict'],
        description: 'How thorough the code review should be'
      },
      {
        key: 'auto_approve',
        label: 'Auto-approve Minor Changes',
        type: 'boolean',
        required: false,
        default: false,
        description: 'Automatically approve PRs with only minor changes'
      }
    ]
  }
];

export const useTemplates = (): UseTemplatesReturn => {
    const [templates, setTemplates] = useState<Template[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [instantiationStatus, setInstantiationStatus] = useState<InstantiationStatus>('idle');
    const [instantiationResult, setInstantiationResult] = useState<TemplateInstantiationResponse | null>(null);
    const { toast } = useToast();
  
    const fetchTemplates = useCallback(async () => {
      try {
        setIsLoading(true);
        setError(null);
  
        try {
          const response = await fetchTemplatesApi();
          setTemplates(response.templates);
          return response.templates;
        } catch (apiError) {
          console.log('API not available, using mock data');
          setTemplates(MOCK_TEMPLATES);
          return MOCK_TEMPLATES;
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || 'Failed to fetch templates';
        setError(errorMessage);
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive'
        });
        console.error('Error fetching templates:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    }, [toast]);
  
    const fetchTemplateById = useCallback(async (id: string) => {
      try {
        setIsLoading(true);
        setError(null);
  
        try {
          const template = await fetchTemplateByIdApi(id);
          setSelectedTemplate(template);
          return template;
        } catch (apiError) {
          const mockTemplate = MOCK_TEMPLATES.find(t => t.id === id);
          if (mockTemplate) {
            setSelectedTemplate(mockTemplate);
            return mockTemplate;
          }
          throw new Error('Template not found');
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || 'Failed to fetch template';
        setError(errorMessage);
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive'
        });
        console.error('Error fetching template:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    }, [toast]);
  
    const instantiateTemplate = useCallback(async (
      templateId: string, 
      inputs: Record<string, any>
    ): Promise<TemplateInstantiationResponse | null> => {
      try {
        setInstantiationStatus('validating');
        setError(null);
  
        await new Promise(resolve => setTimeout(resolve, 500));
        setInstantiationStatus('submitting');
  
        try {
          const result = await instantiateTemplateApi(templateId, inputs);
  
          setInstantiationStatus('provisioning');
          await new Promise(resolve => setTimeout(resolve, 1000));
  
          setInstantiationStatus('finalizing');
          await new Promise(resolve => setTimeout(resolve, 500));
  
          setInstantiationStatus('completed');
          setInstantiationResult(result);
  
          toast({
            title: 'Success',
            description: 'Workflow created successfully!'
          });
  
          return result;
        } catch (apiError) {
          // Fallback to mock mode when API is not available
          setInstantiationStatus('provisioning');
          await new Promise(resolve => setTimeout(resolve, 2000));
  
          setInstantiationStatus('finalizing');
          await new Promise(resolve => setTimeout(resolve, 1000));
  
          const mockResult: TemplateInstantiationResponse = {
            workflow_id: `wf-${Date.now()}`,
            instance_id: `inst-${Date.now()}`,
            created_elements: ['agent-1', 'tool-1', 'retriever-1'],
            status: 'completed',
            chat_endpoint: '/api/chat/session'
          };
  
          setInstantiationStatus('completed');
          setInstantiationResult(mockResult);
  
          toast({
            title: 'Success',
            description: 'Workflow created successfully! (Demo Mode)'
          });
  
          return mockResult;
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || 'Failed to instantiate template';
        setError(errorMessage);
        setInstantiationStatus('failed');
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive'
        });
        console.error('Error instantiating template:', err);
        return null;
      }
    }, [toast]);
  
    const checkInstantiationStatus = useCallback(async (
      instanceId: string
    ): Promise<InstantiationStatusResponse | null> => {
      try {
        const statusResponse = await getInstantiationStatus(instanceId);
        setInstantiationStatus(statusResponse.status);
        return statusResponse;
      } catch (err: any) {
        console.error('Error checking instantiation status:', err);
        return null;
      }
    }, []);
  
    const resetInstantiation = useCallback(() => {
      setInstantiationStatus('idle');
      setInstantiationResult(null);
      setError(null);
    }, []);
  
    const getCategories = useCallback((): TemplateCategory[] => {
      const categoryMap = new Map<string, number>();
      templates.forEach(template => {
        const count = categoryMap.get(template.category) || 0;
        categoryMap.set(template.category, count + 1);
      });
      return Array.from(categoryMap.entries()).map(([name, count]) => ({ name, count }));
    }, [templates]);
  
    const filterTemplates = useCallback((
      searchQuery: string = '',
      category: string | null = null
    ): Template[] => {
      return templates.filter(template => {
        const matchesSearch = !searchQuery || 
          template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          template.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
        
        const matchesCategory = !category || template.category === category;
        
        return matchesSearch && matchesCategory;
      });
    }, [templates]);
  
    return {
      templates,
      selectedTemplate,
      isLoading,
      error,
      instantiationStatus,
      instantiationResult,
      fetchTemplates,
      fetchTemplateById,
      instantiateTemplate,
      checkInstantiationStatus,
      resetInstantiation,
      getCategories,
      filterTemplates,
      setSelectedTemplate
    };
  };

export default useTemplates;

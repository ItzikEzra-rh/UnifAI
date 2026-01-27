import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { 
  ArrowLeft,
  FileText, 
  MessageSquare, 
  Database, 
  GitBranch,
  Clock,
  Zap,
  CheckCircle,
  Key,
  List,
  Settings
} from 'lucide-react';
import { Template, TemplateField } from '@/types/templates';

interface TemplateDetailViewProps {
  template: Template;
  onBack: () => void;
  onGenerate: () => void;
}

const getTemplateIcon = (iconName?: string) => {
  const iconMap: { [key: string]: React.ReactNode } = {
    FileText: <FileText className="h-8 w-8" />,
    MessageSquare: <MessageSquare className="h-8 w-8" />,
    Database: <Database className="h-8 w-8" />,
    GitBranch: <GitBranch className="h-8 w-8" />,
    Zap: <Zap className="h-8 w-8" />
  };
  return iconMap[iconName || 'FileText'] || <FileText className="h-8 w-8" />;
};

const getFieldTypeIcon = (type: string) => {
  switch (type) {
    case 'secret':
      return <Key className="h-4 w-4 text-yellow-500" />;
    case 'string[]':
      return <List className="h-4 w-4 text-blue-500" />;
    case 'boolean':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    default:
      return <Settings className="h-4 w-4 text-gray-500" />;
  }
};

const FieldRequirementBadge: React.FC<{ field: TemplateField }> = ({ field }) => {
  return (
    <div className="flex items-center gap-2 p-3 bg-background-dark rounded-lg border border-gray-800">
      {getFieldTypeIcon(field.type)}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-200">{field.label}</span>
          {field.required && (
            <Badge variant="destructive" className="text-xs px-1.5 py-0">
              Required
            </Badge>
          )}
          <Badge variant="outline" className="text-xs px-1.5 py-0">
            {field.type}
          </Badge>
        </div>
        {field.description && (
          <p className="text-xs text-gray-500 mt-0.5">{field.description}</p>
        )}
      </div>
    </div>
  );
};

export const TemplateDetailView: React.FC<TemplateDetailViewProps> = ({
  template,
  onBack,
  onGenerate
}) => {
  const requiredFields = template.fields.filter(f => f.required);
  const optionalFields = template.fields.filter(f => !f.required);

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <Button 
        variant="ghost" 
        onClick={onBack}
        className="text-gray-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Templates
      </Button>

      <Card className="bg-background-card border-gray-800">
        <CardHeader className="border-b border-gray-800">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center text-white">
              {getTemplateIcon(template.icon)}
            </div>
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl font-heading mb-2">
                    {template.name}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{template.category}</Badge>
                    <Badge variant="secondary" className="bg-gray-800">
                      v{template.version}
                    </Badge>
                    {template.estimated_setup_time && (
                      <span className="flex items-center text-xs text-gray-400">
                        <Clock className="h-3 w-3 mr-1" />
                        {template.estimated_setup_time}
                      </span>
                    )}
                  </div>
                </div>
                <Button 
                  onClick={onGenerate}
                  className="bg-primary hover:bg-primary/90"
                >
                  <Zap className="h-4 w-4 mr-2" />
                  Generate Workflow
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="p-6 space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-3">Description</h3>
            <p className="text-gray-400 leading-relaxed">{template.description}</p>
          </div>

          {template.output_capabilities && template.output_capabilities.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3">What You Get</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {template.output_capabilities.map((capability, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center gap-2 p-3 bg-primary/10 rounded-lg border border-primary/20"
                  >
                    <CheckCircle className="h-5 w-5 text-primary" />
                    <span className="text-sm text-gray-200">{capability}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="text-lg font-medium mb-3">
              Required Inputs
              <span className="text-sm font-normal text-gray-500 ml-2">
                ({requiredFields.length} fields)
              </span>
            </h3>
            <div className="space-y-2">
              {requiredFields.map((field) => (
                <FieldRequirementBadge key={field.key} field={field} />
              ))}
            </div>
          </div>

          {optionalFields.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3">
                Optional Settings
                <span className="text-sm font-normal text-gray-500 ml-2">
                  ({optionalFields.length} fields)
                </span>
              </h3>
              <div className="space-y-2">
                {optionalFields.map((field) => (
                  <FieldRequirementBadge key={field.key} field={field} />
                ))}
              </div>
            </div>
          )}

          {template.tags && template.tags.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {template.tags.map((tag, idx) => (
                  <span 
                    key={idx}
                    className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-full"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default TemplateDetailView;
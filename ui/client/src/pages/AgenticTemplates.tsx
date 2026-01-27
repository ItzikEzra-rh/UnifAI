import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'wouter';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TemplateCatalog,
  TemplateDetailView,
  DynamicFormRenderer,
  InstantiationProgress
} from '@/components/agentic-ai/templates';
import { useTemplates } from '@/hooks/use-templates';
import { Template, TemplateFormData } from '@/types/templates';

type ViewMode = 'catalog' | 'detail' | 'form';

export default function AgenticTemplates() {
  const [, setLocation] = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('catalog');
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);

  const {
    templates,
    isLoading,
    error,
    instantiationStatus,
    instantiationResult,
    fetchTemplates,
    instantiateTemplate,
    resetInstantiation,
    getCategories
  } = useTemplates();

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleSelectTemplate = useCallback((template: Template) => {
    setSelectedTemplate(template);
    setViewMode('detail');
  }, []);

  const handleBackToCatalog = useCallback(() => {
    setViewMode('catalog');
    setSelectedTemplate(null);
  }, []);

  const handleOpenForm = useCallback(() => {
    setIsFormOpen(true);
  }, []);

  const handleCloseForm = useCallback(() => {
    setIsFormOpen(false);
  }, []);

  const handleSubmitForm = useCallback(async (data: TemplateFormData) => {
    if (!selectedTemplate) return;
    
    setIsFormOpen(false);
    await instantiateTemplate(selectedTemplate.id, data);
  }, [selectedTemplate, instantiateTemplate]);

  const handleRetryInstantiation = useCallback(() => {
    resetInstantiation();
    setIsFormOpen(true);
  }, [resetInstantiation]);

  const handleNavigateToWorkflow = useCallback(() => {
    resetInstantiation();
    setLocation('/agentic-ai');
  }, [resetInstantiation, setLocation]);

  const handleNavigateToChat = useCallback(() => {
    resetInstantiation();
    setLocation('/agentic-chats');
  }, [resetInstantiation, setLocation]);

  const handleCloseProgress = useCallback(() => {
    resetInstantiation();
  }, [resetInstantiation]);

  const categories = getCategories();

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title="Agentic AI Templates" 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
        />

        <main className="flex-1 overflow-y-auto bg-background-dark">
          <div className="p-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              {viewMode === 'catalog' && (
                <>
                  <div className="mb-6">
                    <h1 className="text-3xl font-heading font-bold mb-2">
                      Workflow Templates
                    </h1>
                    <p className="text-gray-400">
                      Choose a template to create production-ready agentic workflows in minutes.
                      Each template provides a complete solution that you can customize to your needs.
                    </p>
                  </div>

                  <TemplateCatalog
                    templates={templates}
                    categories={categories}
                    isLoading={isLoading}
                    onSelectTemplate={handleSelectTemplate}
                  />
                </>
              )}

              <AnimatePresence mode="wait">
                {viewMode === 'detail' && selectedTemplate && (
                  <TemplateDetailView
                    key="detail"
                    template={selectedTemplate}
                    onBack={handleBackToCatalog}
                    onGenerate={handleOpenForm}
                  />
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </main>
      </div>

      {selectedTemplate && (
        <DynamicFormRenderer
          template={selectedTemplate}
          isOpen={isFormOpen}
          onClose={handleCloseForm}
          onSubmit={handleSubmitForm}
          isSubmitting={instantiationStatus !== 'idle' && instantiationStatus !== 'completed' && instantiationStatus !== 'failed'}
        />
      )}

      <InstantiationProgress
        status={instantiationStatus}
        result={instantiationResult}
        error={error}
        onClose={handleCloseProgress}
        onRetry={handleRetryInstantiation}
        onNavigateToWorkflow={handleNavigateToWorkflow}
        onNavigateToChat={handleNavigateToChat}
      />
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { useLocation } from "wouter";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GuideRenderer } from "./GuideRenderer";
import { Card, CardContent } from "@/components/ui/card";
import { BookOpen, HelpCircle, FileText, MessageSquare, Workflow, Bot, Brain, Wrench, Search, Server, GitBranch } from "lucide-react";
import { loadGuidesForSection, GuidesByCategory } from "@/utils/guideLoader";

// Category display names and icons for Agentic Inventory
const getCategoryDisplayName = (category: string) => {
  const nameMap: { [key: string]: string } = {
    nodes: 'Agents',
    llms: 'LLMs',
    tools: 'Tools',
    retrievers: 'Retrievers',
    providers: 'Providers',
    conditions: 'Conditions'
  };
  return nameMap[category] || category.charAt(0).toUpperCase() + category.slice(1);
};

const getCategoryIcon = (category: string) => {
  const iconMap: { [key: string]: React.ReactNode } = {
    nodes: <Bot className="h-4 w-4" />,
    llms: <Brain className="h-4 w-4" />,
    tools: <Wrench className="h-4 w-4" />,
    retrievers: <Search className="h-4 w-4" />,
    providers: <Server className="h-4 w-4" />,
    conditions: <GitBranch className="h-4 w-4" />
  };
  return iconMap[category] || <FileText className="h-4 w-4" />;
};

// All available categories for Agentic Inventory (using backend category names)
const AGENTIC_INVENTORY_CATEGORIES = ['conditions', 'llms', 'nodes', 'providers', 'retrievers', 'tools'];

export const GuidesPage: React.FC = () => {
  const [location] = useLocation();
  const [guidesByCategory, setGuidesByCategory] = useState<GuidesByCategory>({});
  const [isLoading, setIsLoading] = useState(true);
  
  // Parse URL params for section and category
  const urlParams = new URLSearchParams(location.split('?')[1] || '');
  const sectionParam = urlParams.get('section') || 'agentic-inventory';
  const categoryParam = urlParams.get('category');
  
  const [activeSection, setActiveSection] = useState<string>(sectionParam);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(categoryParam || null);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      
      // For agentic-inventory, always load all categories but show empty state if no guides
      // For other sections, load all guides
      const guides = await loadGuidesForSection(activeSection);
      setGuidesByCategory(guides);
      
      // Auto-select first category with guides if none selected (for agentic-inventory)
      if (activeSection === 'agentic-inventory' && !selectedCategory) {
        const categoriesWithGuides = Object.keys(guides).filter(cat => guides[cat].length > 0);
        if (categoriesWithGuides.length > 0) {
          setSelectedCategory(categoriesWithGuides[0]);
        } else {
          // If no guides exist, select the first category from the list
          setSelectedCategory(AGENTIC_INVENTORY_CATEGORIES[0]);
        }
      }
      
      setIsLoading(false);
    };
    
    load();
  }, [activeSection]);
  
  // Update selected category when URL param changes
  useEffect(() => {
    if (categoryParam && categoryParam !== selectedCategory) {
      setSelectedCategory(categoryParam);
    }
  }, [categoryParam]);

  // Update URL when section or category changes
  useEffect(() => {
    const newUrl = `/guides?section=${activeSection}${selectedCategory ? `&category=${selectedCategory}` : ''}`;
    if (location !== newUrl) {
      window.history.replaceState({}, '', newUrl);
    }
  }, [activeSection, selectedCategory, location]);

  const categories = Object.keys(guidesByCategory).sort();
  const hasGuides = categories.some(cat => guidesByCategory[cat].length > 0);

  if (isLoading) {
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header title="How-To Guides" onToggleSidebar={() => {}} />
          <main className="flex-1 overflow-y-auto p-6 bg-background-dark">
            <div className="flex items-center justify-center h-64">
              <div className="text-center text-gray-400">
                <p>Loading guides...</p>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="How-To Guides" onToggleSidebar={() => {}} />
        <main className="flex-1 overflow-y-auto p-6 bg-background-dark">
          <Tabs value={activeSection} onValueChange={setActiveSection} className="w-full">
            <TabsList className="mb-6">
              <TabsTrigger value="slack-integration">
                <MessageSquare className="mr-2 h-4 w-4" />
                Slack Integration
              </TabsTrigger>
              <TabsTrigger value="documents">
                <FileText className="mr-2 h-4 w-4" />
                Documents
              </TabsTrigger>
              <TabsTrigger value="agentic-inventory">
                <FileText className="mr-2 h-4 w-4" />
                Agentic Inventory
              </TabsTrigger>
              <TabsTrigger value="agentic-ai-workflows">
                <Workflow className="mr-2 h-4 w-4" />
                Agentic AI Workflows
              </TabsTrigger>
            </TabsList>

            {/* Slack Integration Tab */}
            <TabsContent value="slack-integration" className="space-y-6">
              {!hasGuides ? (
                <Card className="bg-background-card border-gray-800">
                  <CardContent className="p-12 text-center">
                    <HelpCircle className="h-16 w-16 mx-auto mb-4 text-gray-500" />
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      No guides available yet
                    </h3>
                    <p className="text-muted-foreground max-w-md mx-auto">
                      No guides have been created here yet. Feel free to contact us to add guides or check back later.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-6">
                  {categories.map((category) => (
                    guidesByCategory[category].map((guide, index) => (
                      <Card key={index} className="bg-background-card border-gray-800">
                        <CardContent className="p-6">
                          <GuideRenderer
                            title={guide.title}
                            description={guide.description}
                            steps={guide.steps}
                          />
                        </CardContent>
                      </Card>
                    ))
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Documents Tab */}
            <TabsContent value="documents" className="space-y-6">
              {!hasGuides ? (
                <Card className="bg-background-card border-gray-800">
                  <CardContent className="p-12 text-center">
                    <HelpCircle className="h-16 w-16 mx-auto mb-4 text-gray-500" />
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      No guides available yet
                    </h3>
                    <p className="text-muted-foreground max-w-md mx-auto">
                      No guides have been created here yet. Feel free to contact us to add guides or check back later.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-6">
                  {categories.map((category) => (
                    guidesByCategory[category].map((guide, index) => (
                      <Card key={index} className="bg-background-card border-gray-800">
                        <CardContent className="p-6">
                          <GuideRenderer
                            title={guide.title}
                            description={guide.description}
                            steps={guide.steps}
                          />
                        </CardContent>
                      </Card>
                    ))
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Agentic Inventory Tab */}
            <TabsContent value="agentic-inventory" className="space-y-6">
              <Tabs value={selectedCategory || AGENTIC_INVENTORY_CATEGORIES[0]} onValueChange={setSelectedCategory} className="w-full">
                <TabsList className="mb-6">
                  {AGENTIC_INVENTORY_CATEGORIES.map((category) => (
                    <TabsTrigger key={category} value={category}>
                      {getCategoryIcon(category)}
                      <span className="ml-2">{getCategoryDisplayName(category)}</span>
                    </TabsTrigger>
                  ))}
                </TabsList>

                {AGENTIC_INVENTORY_CATEGORIES.map((category) => (
                  <TabsContent key={category} value={category} className="space-y-6">
                    {(() => {
                      const categoryGuides = guidesByCategory[category] || [];
                      const hasCategoryGuides = categoryGuides.length > 0;
                      
                      return hasCategoryGuides ? (
                        <div className="space-y-6">
                          {categoryGuides.map((guide, index) => (
                            <Card key={index} className="bg-background-card border-gray-800">
                              <CardContent className="p-6">
                                <GuideRenderer
                                  title={guide.title}
                                  description={guide.description}
                                  steps={guide.steps}
                                />
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <Card className="bg-background-card border-gray-800">
                          <CardContent className="p-12 text-center">
                            <BookOpen className="h-16 w-16 mx-auto mb-4 text-gray-500" />
                            <h3 className="text-xl font-semibold text-foreground mb-2">
                              No guides available yet
                            </h3>
                            <p className="text-muted-foreground max-w-md mx-auto">
                              No guides have been created here yet. Feel free to contact us to add guides or check back later.
                            </p>
                          </CardContent>
                        </Card>
                      );
                    })()}
                  </TabsContent>
                ))}
              </Tabs>
            </TabsContent>

            {/* Agentic AI Workflows Tab */}
            <TabsContent value="agentic-ai-workflows" className="space-y-6">
              {!hasGuides ? (
                <Card className="bg-background-card border-gray-800">
                  <CardContent className="p-12 text-center">
                    <HelpCircle className="h-16 w-16 mx-auto mb-4 text-gray-500" />
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      No guides available yet
                    </h3>
                    <p className="text-muted-foreground max-w-md mx-auto">
                      No guides have been created here yet. Feel free to contact us to add guides or check back later.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-6">
                  {categories.map((category) => (
                    guidesByCategory[category].map((guide, index) => (
                      <Card key={index} className="bg-background-card border-gray-800">
                        <CardContent className="p-6">
                          <GuideRenderer
                            title={guide.title}
                            description={guide.description}
                            steps={guide.steps}
                          />
                        </CardContent>
                      </Card>
                    ))
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  );
};

export default GuidesPage;

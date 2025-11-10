import React, { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";

interface Step {
  step: number;
  title: string;
  body: string;
}

interface GuideRendererProps {
  steps: Step[];
  title: string;
  description?: string;
}

export const GuideRenderer: React.FC<GuideRendererProps> = ({
  steps,
  title,
  description,
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [commandCopied, setCommandCopied] = useState(false);

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stepNumber)) {
        newSet.delete(stepNumber);
      } else {
        newSet.add(stepNumber);
      }
      return newSet;
    });
  };

  const copyCommandToClipboard = (command: string) => {
    navigator.clipboard.writeText(command).then(() => {
      setCommandCopied(true);
      setTimeout(() => setCommandCopied(false), 2000);
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  const handleDownloadScript = () => {
    const scriptPath = "/guides/local_mcp.sh";
    fetch(scriptPath)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`File not found: ${response.status}`);
        }
        return response.text();
      })
      .then((scriptContent) => {
        const blob = new Blob([scriptContent], { type: "text/plain" });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "local_mcp.txt";
        link.style.display = "none";
        document.body.appendChild(link);
        link.click();
        
        setTimeout(() => {
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        }, 100);
      })
      .catch((error) => {
        console.error("Download failed:", error);
      });
  };

  // Extract code blocks from markdown and handle special actions
  const renderMarkdown = (content: string) => {
    return (
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || "");
            const codeString = String(children).replace(/\n$/, "");
            
            if (!inline && match) {
              // Check if this is a bash script block that should have download button
              const isBashScript = match[1] === "bash" && codeString.includes("local_mcp.sh");
              
              return (
                <div className="relative">
                  <div className="absolute top-2 right-2 flex gap-2 z-10">
                    {isBashScript && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={handleDownloadScript}
                        className="h-7 px-2 text-xs bg-background-dark/80 hover:bg-background-dark"
                        title="Download script"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        Download
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => copyCommandToClipboard(codeString)}
                      className="h-7 px-2 text-xs bg-background-dark/80 hover:bg-background-dark"
                      title="Copy command"
                    >
                      {commandCopied ? (
                        <Check className="w-3 h-3 text-green-400" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </Button>
                  </div>
                  <pre className="bg-background-dark p-4 rounded-md overflow-x-auto">
                    <code className={`language-${match[1]} text-sm font-mono text-foreground`} {...props}>
                      {codeString}
                    </code>
                  </pre>
                </div>
              );
            }
            
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          a({ node, href, children, ...props }: any) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
                {...props}
              >
                {children}
              </a>
            );
          },
          h2({ node, children, ...props }: any) {
            return (
              <h2 className="text-lg font-semibold text-foreground mt-4 mb-2" {...props}>
                {children}
              </h2>
            );
          },
          h3({ node, children, ...props }: any) {
            return (
              <h3 className="text-base font-semibold text-foreground mt-3 mb-2" {...props}>
                {children}
              </h3>
            );
          },
          ul({ node, children, ...props }: any) {
            return (
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground ml-4" {...props}>
                {children}
              </ul>
            );
          },
          ol({ node, children, ...props }: any) {
            return (
              <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground ml-4" {...props}>
                {children}
              </ol>
            );
          },
          li({ node, children, ...props }: any) {
            return (
              <li className="text-sm text-muted-foreground" {...props}>
                {children}
              </li>
            );
          },
          p({ node, children, ...props }: any) {
            return (
              <p className="text-sm text-muted-foreground mb-2" {...props}>
                {children}
              </p>
            );
          },
          strong({ node, children, ...props }: any) {
            return (
              <strong className="font-semibold text-foreground" {...props}>
                {children}
              </strong>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground mb-2">{title}</h1>
        {description && (
          <p className="text-muted-foreground">{description}</p>
        )}
      </div>

      {steps.map((step) => (
        <div
          key={step.step}
          className="border border-gray-700 rounded-md overflow-hidden"
        >
          <button
            type="button"
            onClick={() => toggleStep(step.step)}
            className="w-full flex items-center justify-between p-4 bg-background-dark hover:bg-background-dark/80 transition-colors"
          >
            <span className="text-base font-medium text-foreground">
              Step {step.step}: {step.title}
            </span>
            {expandedSteps.has(step.step) ? (
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            )}
          </button>
          {expandedSteps.has(step.step) && (
            <div className="p-4 bg-background-card border-t border-gray-700">
              <div className="prose prose-invert max-w-none">
                {renderMarkdown(step.body)}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};


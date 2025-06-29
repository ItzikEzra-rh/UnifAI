import { Card, CardContent } from "@/components/ui/card";
import { DocumentData } from "@/documents/DocumentData";
import { ReactNode } from "react";

interface CardContainerProps {
  title?: string; // optional, since you passed empty string before
  children: ReactNode;
  footer?: ReactNode;
  activeDoc: any; // assuming Document is imported from your types
}

export const CardContainer = ({ title, children, footer, activeDoc }: CardContainerProps) => (
  <>
  <Card className="bg-background-card shadow-card border-gray-800">
    <CardContent className="p-6">
      {title && (
        <h2 className="text-xl font-semibold mb-6">
          {title}
        </h2>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {children}
      </div>

      {footer && <div className="mt-6 flex justify-between items-center">{footer}</div>}
    </CardContent>
  </Card>
  {activeDoc && (
                <div className="mt-6">
                  <DocumentData doc={activeDoc} />
                </div>
              )}
              </>
);

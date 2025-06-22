import { Card, CardContent } from "@/components/ui/card";
import { ReactNode } from "react";

interface CardContainerProps {
  title: string;
  children: ReactNode;
  filters?: ReactNode;
  footer?: ReactNode;
  actions?: ReactNode; // <-- Add this
}

export const CardContainer = ({ title, children, filters, footer, actions }: CardContainerProps) => (
  <Card className="bg-background-card shadow-card border-gray-800">
    <CardContent className="p-6">
      <div className="flex items-center justify-between mb-6">
        {/* Left side: actions (e.g. viewButtons), Right side: filters */}
        <div>{actions}</div>
        <div>{filters}</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {children}
      </div>

      {footer && <div className="mt-6 flex justify-between items-center">{footer}</div>}
    </CardContent>
  </Card>
);


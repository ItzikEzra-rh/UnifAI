import { Card, CardContent } from "@/components/ui/card";
import { ReactNode } from "react";

interface CardContainerProps {
  title: string;
  children: ReactNode;
  filters?: ReactNode;
  footer?: ReactNode;
}

export const CardContainer = ({ title, children, filters, footer }: CardContainerProps) => (
  <Card className="bg-background-card shadow-card border-gray-800">
    <CardContent className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-heading font-semibold">{title}</h3>
        {filters}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {children}
      </div>

      {footer && <div className="mt-6 flex justify-between items-center">{footer}</div>}
    </CardContent>
  </Card>
);

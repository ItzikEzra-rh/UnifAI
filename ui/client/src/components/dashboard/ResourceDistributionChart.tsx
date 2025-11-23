import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FaChartPie } from "react-icons/fa";
import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import SimpleTooltip from "@/components/shared/SimpleTooltip";
import { generateColorPalette } from "@/lib/colorUtils";
import { useMemo } from "react";

interface ResourceCategory {
  category: string;
  count: number;
  types: { [type: string]: number };
}

interface ResourceDistributionChartProps {
  data: ResourceCategory[];
  isLoading?: boolean;
  primaryColor?: string;
}

export function ResourceDistributionChart({
  data,
  isLoading = false,
  primaryColor = "#A60000",
}: ResourceDistributionChartProps) {
  const { colorPalette, categoryColorMap } = useMemo(() => {
    const palette = generateColorPalette(primaryColor, data.length);
    const colorMap = new Map<string, string>();
    const sortedCategories = [...data].sort((a, b) => b.count - a.count);

    sortedCategories.forEach((cat, idx) => {
      const colorIndex = Math.min(idx, palette.length - 1);
      colorMap.set(cat.category, palette[colorIndex]);
    });

    return { colorPalette: palette, categoryColorMap: colorMap };
  }, [data, primaryColor]);

  const total = useMemo(
    () => data.reduce((sum, c) => sum + c.count, 0),
    [data]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4 overflow-y-auto flex-1 pr-2 pb-4">
      {data
        .sort((a, b) => b.count - a.count)
        .map((category, idx) => {
          const percentage = total > 0 ? Math.round((category.count / total) * 100) : 0;
          const color =
            categoryColorMap.get(category.category) ||
            colorPalette[idx % colorPalette.length];

          const typeBreakdown = Object.entries(category.types)
            .map(([type, count]) => `${count} ${type}`)
            .join(", ");
          const tooltipContent = typeBreakdown || "No sub-types";

          return (
            <SimpleTooltip
              key={category.category}
              content={<div className="text-sm">{tooltipContent}</div>}
            >
              <div className="space-y-2 max-h-24 overflow-hidden flex flex-col cursor-help">
                <div className="flex items-center justify-between text-sm flex-shrink-0">
                  <span className="text-gray-300 font-medium">
                    {category.category}
                  </span>
                  <span className="text-gray-400">
                    {category.count} ({percentage}%)
                  </span>
                </div>
                <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden flex-shrink-0">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.8, delay: idx * 0.1 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: color }}
                  />
                </div>
              </div>
            </SimpleTooltip>
          );
        })}
    </div>
  );
}


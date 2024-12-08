import React from 'react';
import { PieChart, BarChart, LineChart } from '@mui/x-charts';

const DEFAULT_WIDTH=600;
const DEFAULT_HEIGHT=400;

interface ChartProps {
  type: 'pie' | 'bar' | 'line';
  data: any[];
  title: string;
  label?: string;
  width?: number;
  height?: number;
}

const Charts: React.FC<ChartProps> = ({
  type,
  data,
  title,
  label = '',
  width = DEFAULT_WIDTH,
  height = DEFAULT_HEIGHT
}) => {
  const renderChart = () => {
    switch (type) {
      case 'pie':
        return (
          <PieChart
            series={[{ data }]}
            width={width}
            height={height}
            margin={{ top: 50, bottom: 50, left: 50, right: 50 }}
            slotProps={{
              legend: {
                direction: 'row',
                position: { vertical: 'top', horizontal: 'middle' },
                padding: -10,
                labelStyle: {
                  fontSize: '12px'
                },
              },
            }}
          />
        );
      case 'bar':
        return (
          <BarChart
            xAxis={[{ data: data.map((item: any) => item.label), scaleType: 'band' }]}
            series={[{ data: data.map((item: any) => item.value), label: label }]}
            width={width}
            height={height}
          />
        );
      case 'line':
        return (
          <LineChart
            xAxis={[{ data: data.map((item: any) => item.label), scaleType: 'band' }]}
            yAxis={[{ scaleType: 'linear' }]}
            series={[{ data: data.map((item: any) => item.value), label: label }]}
            width={width}
            height={height}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="graph-container">
      <h3>{title}</h3>
      {renderChart()}
    </div>
  );
};

export default Charts;

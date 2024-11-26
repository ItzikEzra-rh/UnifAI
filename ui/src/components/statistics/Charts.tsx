import React from 'react';
import { PieChart, BarChart, LineChart } from '@mui/x-charts';
import { string } from 'yup';

interface ChartProps {
  type: 'pie' | 'bar' | 'line';  
  data: any[];  
  width?: number;  
  height?: number;  
  title: string;  
  label?: string;
}

const Charts: React.FC<ChartProps> = ({
  type,
  data,
  title,
  label
}) => {
  const renderChart = () => {
    switch (type) {
      case 'pie':
        return (
          <PieChart
            series={[{ data }]}
            width={600}
            height={400}
            margin={{ top: 50, bottom: 50, left: 50, right:50 }}
            slotProps={{
              legend: {
                direction: 'row',
                position: { vertical: 'top', horizontal: 'middle' },
                padding: 0,
                labelStyle: {
                  fontSize: '12px', // Adjust the font size here
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
            width={600}
            height={400}
          />
        );
      case 'line':
        return (
          <LineChart
            xAxis={[{ data: data.map((item: any) => item.label), scaleType: 'band' }]}
            yAxis={[{ scaleType: 'linear' }]}
            series={[{ data: data.map((item: any) => item.value), label: label }]}
            width={600}
            height={400}
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

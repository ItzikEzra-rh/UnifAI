import React, { useEffect, useState } from 'react';
import axios from '../../http/axiosLLMConfig';
import { Line, Bar } from 'react-chartjs-2';
import { PieChart } from '@mui/x-charts/PieChart';
import 'chart.js/auto';
import '../../styles.css';

interface ModelData {
  id: string;
  contextLength: number;
  modelName: string;
  modelType: string;
  project: string;
}

const StatisticsGraphs: React.FC = () => {
  const [data, setData] = useState<ModelData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/backend/getModels');
        const transformedData = response.data.map((item: any) => ({
          id: item._id,
          contextLength: item.context_length,
          modelName: item.base_model,
          modelType: item.model_type,
          project: item.project,
        }));
        setData(transformedData);
      } catch (error) {
        console.error('Error fetching model data:', error);
      }
    };

    fetchData();
  }, []);

  const getProjectsData = () => {
    const projectCounts = data.reduce((acc: Record<string, number>, item) => {
      acc[item.project] = (acc[item.project] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(projectCounts).map(([key, value]) => ({
      id: key,
      value,
    }));
  };


  const getModelNameData = () => {
    const modelNameCounts = data.reduce((acc: Record<string, number>, item) => {
      acc[item.modelName] = (acc[item.modelName] || 0) + 1;
      return acc;
    }, {});
  
    return Object.entries(modelNameCounts).map(([key, value]) => ({
      id: key,
      value,
    }));
  };
  

  const getLineChartData = () => {
    return {
      labels: data.map(item => item.modelName),
      datasets: [
        {
          label: 'Context Length',
          data: data.map(item => item.contextLength),
          backgroundColor: '#ffffff',  // Point fill color (inside)
          borderColor: '#ffffff',      // Point border color
          borderWidth: 3,              // Increase border thickness for visibility
          pointBorderColor: '#ffffff', // White border color for dark mode
          pointBackgroundColor: '#36A2EB', // Point fill color
          pointBorderWidth: 3,         // Increase border width
          pointRadius: 8,              // Increase point size for visibility
          fill: false,
          showLine: false,             // No connecting line between points
        },
      ],
    };
  };

  const getBarChartData = () => {
    return {
      labels: data.map(item => item.modelName),
      datasets: [
        {
          label: 'Context Length',
          data: data.map(item => item.contextLength),
          backgroundColor: '#ffffff', // Bar color (white for dark mode)
          borderColor: '#ffffff',
          borderWidth: 1,
        },
      ],
    };
  };  

  return (
    <div className="statistics-graphs">

      <div className="graph-row">
        <div className="graph-container">
          <h3>Project Distribution</h3>
          <PieChart series={[{data: getProjectsData()}]} 
            slotProps={{
              legend: {
                hidden: false,
                direction: 'column',
                position: { vertical: 'top', horizontal: 'middle' },
                padding: 0,
              },
            }}
          />
        </div>
        <div className="graph-container">
          <h3>Model Name Distribution</h3>
          <PieChart series={[{data: getModelNameData()}
          ]} slotProps={{
            legend: {
              direction: 'column',
              position: { vertical: 'top', horizontal: 'middle' },
              padding: 0,
            },
          }}/>
        </div>
      </div>

      <div className="graph-row">
        <div className="graph-container">
            <h3>Context Length by Project</h3>
            <Bar data={getBarChartData()}/>
        </div>
        <div className="graph-container">
          <h3>Context Length by Project</h3>
          <Line data={getLineChartData ()} />
        </div>
      </div>

    </div>
  );
};

export default StatisticsGraphs;
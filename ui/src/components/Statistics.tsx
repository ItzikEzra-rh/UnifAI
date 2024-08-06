import React, { useEffect, useState } from 'react';
import axios from '../http/axiosLLMConfig';
import { Pie, Line, Bar } from 'react-chartjs-2';
import 'chart.js/auto';
import '../styles.css';

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
          modelName: item.model_name,
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

    return {
      labels: Object.keys(projectCounts),
      datasets: [
        {
          data: Object.values(projectCounts),
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
        },
      ],
    };
  };

  const getModelNameData = () => {
    const modelNameCounts = data.reduce((acc: Record<string, number>, item) => {
      acc[item.modelName] = (acc[item.modelName] || 0) + 1;
      return acc;
    }, {});

    return {
      labels: Object.keys(modelNameCounts),
      datasets: [
        {
          data: Object.values(modelNameCounts),
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
        },
      ],
    };
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
          <Pie data={getProjectsData()} />
        </div>
        <div className="graph-container">
          <h3>Model Name Distribution</h3>
          <Pie data={getModelNameData()} />
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
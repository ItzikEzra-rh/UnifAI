import React, { useEffect, useState } from 'react';
import axios from '../../http/axiosLLMConfig';
import { PieChart, BarChart, LineChart } from '@mui/x-charts';
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

  const getBarChartData = () => {
    const projects = Array.from(new Set(data.map((item) => item.project)));
    const contextLengths = projects.map((project) =>
      data
        .filter((item) => item.project === project)
        .reduce((sum, item) => sum + item.contextLength, 0)
    );
    return { projects, contextLengths };
  };

  const getLineChartData = () => {
    const modelNames = data.map((item) => item.modelName); 
    const contextLengths = data.map((item) => item.contextLength); 
    return { modelNames, contextLengths };
  };



  return (
    <div className="statistics-graphs">
      <div className="graph-row">
        <div className="graph-container">
          <h3>Project Distribution</h3>
          <PieChart
            series={[{ data: getProjectsData() }]}
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
          <PieChart
            series={[{ data: getModelNameData() }]}
            slotProps={{
              legend: {
                direction: 'column',
                position: { vertical: 'top', horizontal: 'middle' },
                padding: 0,
              },
            }}
          />
        </div>
      </div>
      <div className="graph-row">
        <div className="graph-container">
          <h3>Context Length by Project</h3>
          <BarChart
            xAxis={[{data: getBarChartData().projects, scaleType: 'band'}]}
            series={[{data: getBarChartData().contextLengths, label: 'Context Length'}]}
            width={600}
            height={400}
          />
        </div>
        <div className="graph-container">
          <h3>Context Length by Model</h3>
          <LineChart
            xAxis={[{data: getLineChartData().modelNames, scaleType: 'band'}]}
            yAxis={[{scaleType: 'linear'}]}
            series={[{data: getLineChartData().contextLengths, label: 'Context Length'}]}
            width={600} 
            height={300} 
          />
        </div>
      </div>
    </div>
  );
};

export default StatisticsGraphs;

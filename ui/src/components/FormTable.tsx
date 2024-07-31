import React, { useEffect, useState } from 'react';
import { useTable, useSortBy, Column } from 'react-table';
import axios from '../http/axiosLLMConfig';
import '../styles.css';
import {TableFormData} from './types/constants'
import { FaPlay, FaSpinner, FaCheck } from 'react-icons/fa';

// Reusable table component
const ModelsTable: React.FC<{ data: TableFormData[], title: string }> = ({ data, title }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Initial': return 'grey';
      case 'Progress': return 'orange';
      case 'Finished': return 'green';
      default: return '';
    }
  };

  const getStatusIcon  = (status: string) => {
    switch (status) {
      case 'Initial': return <FaPlay style={{ color: 'grey' }} />;
      case 'Progress': return <FaSpinner style={{ color: 'orange' }} />;
      case 'Finished': return <FaCheck style={{ color: 'green' }} />;
      default: return null;
    }
  };

  const columns: Column<TableFormData>[] = React.useMemo(
    () => [
      { Header: 'Project Name', accessor: 'projectName', Cell: ({ row }: any) => (
          <span className={`project-name ${row.values.projectName}`}>
            {row.values.projectName}
          </span>
        )
      },
      { Header: 'Training Name', accessor: 'trainingName' },
      { Header: 'Base Model Name', accessor: 'baseModelName' },
      { Header: 'Tests Code Framework', accessor: 'testsCodeFramework' },
      { Header: 'Status', accessor: 'status', Cell: ({ value }) => (
          <span style={{ color: getStatusColor(value) }}>
            {getStatusIcon(value)} {value}
          </span>
        ),
      },
      { Header: 'Progress', accessor: 'progress' },
    ],
    []
  );

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } = useTable({ columns, data }, useSortBy);

  return (
    <div className="table-container">
      <h2>{title}</h2>
      <table {...getTableProps()} className="forms-table">
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column: any) => (
                <th {...column.getHeaderProps(column.getSortByToggleProps())}>
                  {column.render('Header')}
                  <span>
                    {column.isSorted
                      ? column.isSortedDesc
                        ? ' 🔽'
                        : ' 🔼'
                      : ''}
                  </span>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map(cell => (
                  <td
                    {...cell.getCellProps()}
                    className="table-cell"
                    onMouseEnter={(e) => {
                      const columnIndex = cell.column.id;
                      const cells = document.querySelectorAll(`td[data-column-id="${columnIndex}"]`);
                      cells.forEach(cell => (cell as HTMLElement).style.backgroundColor = 'rgba(46, 120, 199, 0.2)');
                    }}
                    onMouseLeave={(e) => {
                      const columnIndex = cell.column.id;
                      const cells = document.querySelectorAll(`td[data-column-id="${columnIndex}"]`);
                      cells.forEach(cell => (cell as HTMLElement).style.backgroundColor = '');
                    }}
                    data-column-id={cell.column.id}
                  >
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};


const FormsTable: React.FC = () => {
  const [data, setData] = useState<TableFormData[]>([]);

  const getStatusAndProgress = (modelType: string) => {
    switch (modelType) {
      case 'finetuned': return { status: 'Finished', progress: '100%' };
      case 'foundational': return { status: 'Finished', progress: '100%' };
      case 'checkpoint': return { status: 'Progress', progress: '50%' };
      default: return { status: 'Initial', progress: '0%' };
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/backend/getModels');
        const transformedData = response.data.map((item: any) => {
          const { status, progress } = getStatusAndProgress(item.model_type);
          return {
            projectName: item.project,
            trainingName: 'NCS-24',
            contextLength: item.context_length,
            baseModelName: item.model_name,
            modelType: item.model_type,
            testsCodeFramework: 'Robot',
            status,
            progress,
          };
        });
        setData(transformedData);
      } catch (error) {
        console.error('Error fetching model data:', error);
      }
    };

    fetchData();
  }, []);

  const fineTunedModels = data.filter(model => model.modelType === 'finetuned' || model.modelType === 'checkpoint');
  const foundationalModels = data.filter(model => model.modelType === 'foundational');

  const TableToolTip = () => 
    <div className="tooltip-container">
      <h3 className="tooltip-header">Status Explanation</h3>
      <ul className="tooltip-list">
        <li><FaPlay style={{ color: 'grey' }} /> <strong style={{ color: 'grey' }}>Initial:</strong> Creating a dedicated project-specific parser to create a dataset to train the LLM with.</li>
        <li><FaSpinner style={{ color: 'orange' }} /> <strong style={{ color: 'orange' }}>Progress:</strong> Training the LLM with the new dataset.</li>
        <li><FaCheck style={{ color: 'green' }} /> <strong style={{ color: 'green' }}>Finished:</strong> LLM fine-tuned model is ready to use.</li>
      </ul>
    </div>

  return (
    <div className="table-container">
      <ModelsTable data={fineTunedModels} title="Fine Tuned Models" />
      <ModelsTable data={foundationalModels} title="Foundational Models" />
      <TableToolTip/>
    </div>
  );
};

export default FormsTable;

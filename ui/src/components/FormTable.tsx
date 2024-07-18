import React, { useEffect, useState } from 'react';
import { useTable, useSortBy, Column } from 'react-table';
import axios from '../http/axiosConfig';
import '../styles.css';
import {TableFormData} from './types/constants'
import { FaPlay, FaSpinner, FaCheck } from 'react-icons/fa';

const FormsTable: React.FC = () => {
  const [data, setData] = useState<TableFormData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const initalData = [
        {projectName: 'NCS', trainingName: 'NCS-24', gitPath: 'https://gitlab.ncs', gitCredentialKey: 'UNKNOWN', baseModelName: 'Lama', testsCodeFramework: 'Robot', status: 'Initial', progress: '0%'},
        {projectName: 'CBIS', trainingName: 'CBIS-24', gitPath: 'https://gitlab.cbis', gitCredentialKey: 'UNKNOWN', baseModelName: 'Mistarl', testsCodeFramework: 'Robot', status: 'Progress', progress: '50%'},
        {projectName: 'NCS', trainingName: 'NCS-24-1', gitPath: 'https://gitlab.ncs', gitCredentialKey: 'UNKNOWN', baseModelName: 'Lama', testsCodeFramework: 'Robot', status: 'Progress', progress: '75%'},
        {projectName: 'NCS', trainingName: 'NCS-24-2', gitPath: 'https://gitlab.ncs', gitCredentialKey: 'UNKNOWN', baseModelName: 'Lama', testsCodeFramework: 'Robot', status: 'Finished', progress: '100%'}
      ]
      setData(initalData)
      // try {
      //   const response = await axios.get<TableFormData[]>('/api/forms');
      //   setData(response.data);
      // } catch (error) {
      //   console.error('Error fetching data', error);
      // }
    };

    fetchData();
  }, []);

  const getStatusIcon  = (status: string) => {
    switch (status) {
      case 'Initial': return <FaPlay style={{ color: 'grey' }} />;
      case 'Progress': return <FaSpinner style={{ color: 'orange' }} />;
      case 'Finished': return <FaCheck style={{ color: 'green' }} />;
      default: return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Initial': return 'grey';
      case 'Progress': return 'orange';
      case 'Finished': return 'green';
      default: return '';
    }
  };

  const columns: Column<FormData>[] = React.useMemo(
    () => [
      { Header: 'Project Name', accessor: 'projectName', Cell: ({ row }: any) => (
          <span className={`project-name ${row.values.projectName}`}>
            {row.values.projectName}
          </span>
        )
      },
      { Header: 'Training Name', accessor: 'trainingName' },
      { Header: 'Git Path to Expand From', accessor: 'gitPath' },
      { Header: 'Git Credential Key', accessor: 'gitCredentialKey' },
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

  const tableInstance = useTable({ columns, data }, useSortBy);

  const TableToolTip = () => 
    <div className="tooltip-container">
      <h3>Status Explanation</h3>
      <ul>
        <li><FaPlay style={{ color: 'grey' }} /> <strong style={{ color: 'grey' }}>Initial:</strong> Creating a dedicated project-specific parser to create a dataset to train the LLM with.</li>
        <li><FaSpinner style={{ color: 'orange' }} /> <strong style={{ color: 'orange' }}>Progress:</strong> Training the LLM with the new dataset.</li>
        <li><FaCheck style={{ color: 'green' }} /> <strong style={{ color: 'green' }}>Finished:</strong> LLM fine-tuned model is ready to use.</li>
      </ul>
    </div>
  

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = tableInstance;

  return (
    <div className="table-container">
      <table {...getTableProps()} className="forms-table">
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
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
      <TableToolTip/>
    </div>
  );
};

export default FormsTable;

import React, { useEffect, useState } from 'react';
import { useTable, useSortBy, Column } from 'react-table';
import axios from '../http/axiosLLMConfig';
import { FaDownload } from 'react-icons/fa';
import '../styles.css';

interface RepoFileData {
  name: string;
}

const DataSetTable: React.FC = () => {
  const [data, setData] = useState<RepoFileData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/backend/getHfRepoFiles?repoId=oodeh/NcsRobotTestFramework&repoType=dataset');
        // Convert the array of file names to an array of objects with a 'name' property
        const transformedData = response.data.map((fileName: string) => ({ name: fileName }));
        setData(transformedData);
      } catch (error) {
        console.error('Error fetching repository files:', error);
      }
    };

    fetchData();
  }, []);

  const columns: Column<RepoFileData>[] = React.useMemo(
    () => [
      {
        Header: 'Name',
        accessor: 'name',
        id: 'fileName',  // Assign a unique id to this column
      },
      {
        Header: 'Download',
        accessor: 'name',
        id: 'download',  // Assign a unique id to this column
        Cell: ({ value }) => (
          <a href={`/download/${value}`} download>
            <FaDownload />
          </a>
        ),
      },
    ],
    []
  );

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } = useTable({ columns, data }, useSortBy);

  return (
    <div className="table-container">
      <h2>Dataset Files</h2>
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

export default DataSetTable;
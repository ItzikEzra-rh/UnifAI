import React, { useEffect, useState } from 'react';
import { useTable, useSortBy, Column } from 'react-table';
import axios from '../../http/axiosLLMConfig';
import { FaEye } from 'react-icons/fa';
import '../styles.css';

interface RepoFileData {
  name: string;
}

const DataSetTable: React.FC = () => {
  const [data, setData] = useState<RepoFileData[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

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
        Header: 'View',
        accessor: 'name',
        id: 'view',  // Assign a unique id to this column
        Cell: ({ value }) => (
          <span onClick={() => setSelectedFile(value)} style={{ cursor: 'pointer' }}>
            <FaEye />
          </span>
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
      
      {selectedFile && (
        <div className="iframe-container">
          <iframe
            src={`https://huggingface.co/datasets/oodeh/NcsRobotTestFramework/embed/viewer?file=${encodeURIComponent(selectedFile)}`}
            frameBorder="0"
            width="100%"
            height="560px"
          ></iframe>
        </div>
      )}
    </div>
  );
};

export default DataSetTable;
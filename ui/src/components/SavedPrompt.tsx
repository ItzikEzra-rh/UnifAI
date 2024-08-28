import React, { useState, useEffect } from 'react';
import { useTable, useSortBy, Column } from 'react-table';
import { IconButton, Modal, Box, Typography } from '@mui/material';
import { FaFileAlt, FaEdit } from 'react-icons/fa';
import axios from '../http/axiosConfig';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import { github } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css'; // Import Quill styles
import '../styles.css';

// Register the language
SyntaxHighlighter.registerLanguage('python', python);

interface SavedPromptData {
  modelId: string;
  trainingName: string;
  promptText: string;
  comment: string;
}

interface CodeSectionProps {
  title: string;
  content: string;
}

const CodeSection: React.FC<CodeSectionProps> = ({ title, content }) => (
  <div>
    <Typography variant="h6" style={{fontFamily: "ui-monospace"}} gutterBottom>
      {title}
    </Typography>
    <SyntaxHighlighter language="python" style={github}>
      {content || ''}
    </SyntaxHighlighter>
  </div>
);

const SavedPrompts: React.FC = () => {
  const [data, setData] = useState<SavedPromptData[]>([]);
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [commentData, setCommentData] = useState<{ modelId: string, comment: string } | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  
  const settingsIndex = promptText.indexOf('*** Settings ***:');
  const [questionPart, setQuestionPart] = useState<string>(''); // Include the '*** Settings ***:' in the question part
  const [answerPart, setAnswerPart] = useState<string>(''); // Start after '*** Settings ***:' for the answer part

  const columns: Column<SavedPromptData>[] = React.useMemo(
    () => [
      { Header: 'Training Name', accessor: 'trainingName' },
      {
        Header: 'Prompt Text',
        accessor: 'promptText',
        Cell: ({ row }: any) => (
          <IconButton onClick={() => handleOpen(row.original.promptText)}>
            <FaFileAlt />
          </IconButton>
        ),
      },
      {
        Header: 'Comment',
        accessor: 'comment',
        Cell: ({ row }: any) => (
          <>
            <IconButton onClick={() => handleEditOpen(row.original)}>
              <FaEdit />
            </IconButton>
          </>
        ),
      },
    ],
    []
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/backend/retrievePrompt');
        setData(response.data.result);
      } catch (error) {
        console.error('Error fetching saved prompts:', error);
      }
    };

    fetchData();
  }, []);

  const handleOpen = (promptText: string) => {
    setSelectedPrompt(promptText);
    setQuestionPart(promptText.substring(0, settingsIndex + 17))
    setAnswerPart(promptText.substring(settingsIndex + 17))
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedPrompt(null);
  };

  const handleEditOpen = (row: SavedPromptData) => {
    setCommentData({ modelId: row.modelId, comment: row.comment });
    setEditOpen(true);
  };
  
  const handleEditClose = () => {
    setEditOpen(false);
    setCommentData(null);
  };
  
  const handleSaveComment = async () => {
    if (commentData) {
      try {
        await axios.post('/api/backend/savePromptComment', { modelId: commentData.modelId, comment: commentData.comment });
        // Update the data state with the new comment
        setData(prevData =>
          prevData.map(item => item.modelId === commentData.modelId ? { ...item, comment: commentData.comment } : item)
        );
        handleEditClose();
      } catch (error) {
        console.error('Error saving comment:', error);
      }
    }
  };

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } = useTable(
    { columns, data },
    useSortBy
  );

  return (
    <div className="table-container">
      <h2>Saved Prompts</h2>
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
                  <td {...cell.getCellProps()} className="table-cell">
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      <Modal open={open} onClose={handleClose}>
        <Box
            sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 800,
            bgcolor: 'background.paper',
            border: '2px solid #000',
            boxShadow: 24,
            overflowY: 'auto',
            overflowX: 'hidden',
            maxWidth: '80%',
            maxHeight: '80%',
            p: 4,
            }}
        >
            <div className="code-visualizer">
              <CodeSection title="User Question" content={questionPart} />
              <CodeSection title="LLM Answer" content={answerPart} />
            </div>
        </Box>
      </Modal>
      <Modal open={editOpen} onClose={handleEditClose}>
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 800,
            bgcolor: 'background.paper',
            border: '2px solid #000',
            boxShadow: 24,
            p: 4,
          }}
        >
          <ReactQuill value={commentData?.comment || ''} onChange={(value: string) => setCommentData({ ...commentData, comment: value, modelId: commentData?.modelId || '' })} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <button onClick={handleEditClose}>Cancel</button>
            <button onClick={handleSaveComment} style={{ marginLeft: 8 }}>Save</button>
          </Box>
        </Box>
      </Modal>
    </div>
  );
};

export default SavedPrompts;

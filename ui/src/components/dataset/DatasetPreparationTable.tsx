import React, { useEffect, useState } from 'react';
import { Box, Button, IconButton, Modal, LinearProgress, Table, TableBody, TableCell, TableHead, TableRow, TableSortLabel, Typography, Tooltip } from '@mui/material'; 
import axios from '../../http/axiosConfig';
import DeleteIcon from '@mui/icons-material/Delete';
import CancelIcon from '@mui/icons-material/Cancel';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import DescriptionIcon from '@mui/icons-material/Description'; // Import file icon
import '../../styles.css';
import ProgressDisplay from './ProgressDisplay';
import moment from 'moment';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

interface UninstallModalProps {
  datasetId: string;
  status: string;
  handleUninstallConfirm: (datasetId: string, setOpen: ((open: boolean) => void)) => Promise<void>;
}

interface RemoveModalProps {
  datasetId: string;
  status: string;
  handleRemoveConfirm: (datasetId: string, setOpen: ((open: boolean) => void)) => Promise<void>;
}

const UninstallModal: React.FC<UninstallModalProps> = ({ datasetId, status, handleUninstallConfirm }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const disabled = status === "DONE" || status === "UNINSTALLED"
  const title = disabled ? "Deployment has already been uninstalled" : "Trigger uninstall of the helm proccess"

  const handleConfirmClick = async () => {
    setLoading(true);
    await handleUninstallConfirm(datasetId, setOpen);
    setLoading(false);
  };

  return (
    <>
    <Box display="flex" alignItems="center" gap={1}>
        <Tooltip title={title}>
          <span> 
            <IconButton onClick={() => setOpen(true)} sx={{ color: 'red' }} disabled={disabled}>
              <CancelIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

    <Modal open={open} onClose={() => setOpen(false)}>
      <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'background.paper', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', p: 3 }}>
        <Typography variant="h6" component="h2" sx={{ mb: 2, fontWeight: 500, color: '#1a1a1a' }}>
          Are you sure you want to uninstall?
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3, pt: 2, borderTop: '1px solid #eaeaea' }}>
          <Button onClick={() => setOpen(false)} disabled={loading} style={{padding: '8px 16px', borderRadius: '6px', border: '1px solid #e0e0e0', backgroundColor: '#ffffff', color: '#666666', cursor: 'pointer', transition: 'all 0.2s', fontWeight: 500}}>
            No
          </Button>
          <Button onClick={handleConfirmClick} disabled={loading} style={{padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: '#dc2626', color: 'white', cursor: 'pointer', transition: 'all 0.2s', fontWeight: 500,}}>
            {loading ? 'Uninstalling...' : 'Yes'}
          </Button>
        </Box>
      </Box>
    </Modal>
  </>  
  );
};

const RemoveModal: React.FC<RemoveModalProps> = ({ datasetId, status, handleRemoveConfirm }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const enabled = status === "DONE" || status === "UNINSTALLED"
  const title = enabled ? "Remove this proccess from the table" : "You can't remove this row before the deployment is uninstalled"

  const handleConfirmClick = async () => {
    setLoading(true);
    await handleRemoveConfirm(datasetId, setOpen);
    setLoading(false);
  };

  return (
    <>
    <Box display="flex" alignItems="center" gap={1}>
        <Tooltip title={title}>
          <span> 
            <IconButton onClick={() => setOpen(true)} sx={{ color: 'red' }} disabled={!enabled}>
            <DeleteIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

    <Modal open={open} onClose={() => setOpen(false)}>
      <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'background.paper', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', p: 3 }}>
        <Typography variant="h6" component="h2" sx={{ mb: 2, fontWeight: 500, color: '#1a1a1a' }}>
          Are you sure you want to remove this deployment from the table?
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3, pt: 2, borderTop: '1px solid #eaeaea' }}>
          <Button onClick={() => setOpen(false)} disabled={loading} style={{padding: '8px 16px', borderRadius: '6px', border: '1px solid #e0e0e0', backgroundColor: '#ffffff', color: '#666666', cursor: 'pointer', transition: 'all 0.2s', fontWeight: 500}}>
            No
          </Button>
          <Button onClick={handleConfirmClick} disabled={loading} style={{padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: '#dc2626', color: 'white', cursor: 'pointer', transition: 'all 0.2s', fontWeight: 500,}}>
            {loading ? 'Removing...' : 'Yes'}
          </Button>
        </Box>
      </Box>
    </Modal>
  </>  
  );
};

const StatisticsModal = (datasetDetails: any) => {
  const [open, setOpen] = useState(false);
  const disabled = datasetDetails.metrics?.mongodb
  const title = disabled ? "Statistics will be available shortly" : "Display more statistics"

  return (
    <>
      <Box display="flex" alignItems="center" gap={1}>
        <Tooltip title={title}>
          <span> 
            <IconButton onClick={() => setOpen(true)} sx={{ color: 'red' }} disabled={disabled}>
              <ShowChartIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
  
      <Modal open={open} onClose={() => setOpen(false)}>
        <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', height: '60%', width: '65%', bgcolor: 'background.paper' }}>
          <ProgressDisplay datasetDetails={datasetDetails.datasetDetails} />
        </Box>
      </Modal>
    </>
  );
};

const ConfigModal = ({ datasetId }: { datasetId: string }) => {
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await axios.get(`/api/dpr/getConfigFile`, { params: { id: datasetId } });
        setConfig(response.data || {});
      } catch (error) {
        console.error('Error fetching config:', error);
      }
    };

    if (open) {
      fetchConfig();
    }
  }, [open, datasetId]);

  return (
    <>
      <IconButton onClick={() => setOpen(true)} sx={{ color: 'red' }} title="Display configuration json file">
        <DescriptionIcon />
      </IconButton>
      <Modal open={open} onClose={() => setOpen(false)}>
        <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', height: '70%', width: '80%', bgcolor: 'background.paper', padding: 3, overflow: 'auto' }}>
          <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
            Dataset Config
          </Typography>
          <SyntaxHighlighter language="json" style={atomOneDark}>
            {JSON.stringify(config, null, 2)}
          </SyntaxHighlighter>
        </Box>
      </Modal>
    </>
  );
};

const DatasetPreparationTable: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [currentlyRunningDatasets, setCurrentlyRunningDatasets] = useState<any[]>([]);
  const [orderBy, setOrderBy] = useState('Start Time');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');

  const fetchListData = async () => {
    try {
      const response = await axios.get('/api/dpr/notDeletedDeployment');
      if (Array.isArray(response.data)) {
        setDatasets(response.data); 
      } else {
        console.error("Expected array but got:", response.data);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };
  
  useEffect(() => {
    fetchListData();
  }, [currentlyRunningDatasets.length]);

  useEffect(() => {
    const fetchMetrics = async () => {
        try {
            const runningResponse = await axios.get('/api/dpr/currentlyRunningDeployment');
            const runningDatasets = runningResponse.data;
            setCurrentlyRunningDatasets(runningDatasets);

            const currentlyRunningIds = new Set(runningDatasets.map((item: any) => item._id));

            const promises = datasets.map(async (item) => {
                if (!currentlyRunningIds.has(item._id)) {
                    return item; // If not running, keep the item as is
                }

                // Fetch metrics only for running datasets
                const response = await axios.get(`/api/dpr/metrics`, { params: { id: item._id } });
                const data = response.data.data;
                const progressData = data.mongodb ? data.mongodb.find((entry: any) => entry._id === 'progress_data') : {};
                const pass = progressData?.prompts_pass || 0;
                const fail = progressData?.prompts_failed || 0;

                return {
                    ...item,
                    metrics: data,
                    promptsProgress: {
                        pass,
                        fail,
                    },
                };
            });

            // If there are no running datasets, don't overwrite datasets, just keep existing
            if (runningDatasets.length === 0) {
                fetchListData();
            } else {
                // Update datasets with the new progress only for running datasets
                const updatedProgress = await Promise.all(promises);
                setDatasets(updatedProgress);
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    };

    // Only fetch metrics if there is at least one dataset
    if (datasets.length > 0) {
        fetchMetrics(); // Initial fetch
        const intervalId = setInterval(fetchMetrics, 30000); // Re-fetch every 30 seconds
        return () => clearInterval(intervalId); // Clean up the interval on unmount
    }
}, [currentlyRunningDatasets.length]); // Trigger when datasets change


  const handleUninstallConfirm = async (datasetId: string, setOpen: ((open: boolean) => void)) => {
    if (datasetId) {
      try {
        await axios.get('/api/dpr/uninstall', { params: {id: datasetId, status: "UNINSTALLED"} });
        setOpen(false);
        fetchListData();
      } catch (error) {
        console.error('Error deleting prompt:', error);
      }
    }
  };

  const handleRemoveConfirm = async (datasetId: string, setOpen: ((open: boolean) => void)) => {
    if (datasetId) {
      try {
        await axios.get('/api/dpr/delete', { params: {id: datasetId} });
        setOpen(false);
        fetchListData();
      } catch (error) {
        console.error('Error deleting prompt:', error);
      }
    }
  };

  const handleRequestSort = (property: any) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const widthByColumns = {
    'Dataset Name': '25%',
    'Start Time': '25%',
    'Progress': '42%',
    'Statistics': '2%',
    'Config': '2%', 
    'Cancel': '2%',
    'Remove': '2%'
  }

  const displayNameByColumns = {
    'Dataset Name': 'Dataset Name',
    'Start Time': 'Start Time',
    'Progress': 'Progress',
    'Statistics': '',
    'Config': '', 
    'Cancel': '',
    'Remove': ''
  }

  return (
    <Box className="form-container">
      <Table className="forms-table">
        <TableHead>
          <TableRow>
            {(['Dataset Name', 'Start Time', 'Progress', 'Statistics', 'Config', 'Cancel', 'Remove'] as const).map((column) => (
              <TableCell key={column} sx={{ borderRight: '1px solid #ddd', width: widthByColumns[column] }}>
                <TableSortLabel
                  active={orderBy === column}
                  direction={orderBy === column ? order : 'asc'}
                  onClick={() => handleRequestSort(column)}
                >
                  {displayNameByColumns[column]}
                </TableSortLabel>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {datasets?.map((row) => {
            // Calculate the progress percentage for each row
            const progressData = row.metrics?.mongodb?.find((item: any) => item._id === 'progress_data');
            const progressPercentage = (progressData?.prompts_processed / progressData?.number_of_prompts) * 100 || 0;
            const passed = progressData?.prompts_pass || 0;
            const failed = progressData?.prompts_failed || 0;
            const remaining = progressData?.number_of_prompts - progressData?.prompts_processed;
            const displayRemaining = remaining ?? 'TBD';
            return (
              <TableRow key={row._id}>
                <TableCell>{row.name}</TableCell>
                <TableCell>{moment(row.first_deployed).format("MMM DD, YYYY [at] hh:mm A")}</TableCell>
                <TableCell>
                  <Box sx={{ width: '100%', mt: 2 }}>
                  <Tooltip title={<p className="custom-tooltip-text">Passed Prompts: {passed}, Failed Prompts: {failed}, Remaining: {displayRemaining}</p>} classes={{ tooltip: "custom-tooltip" }}>
                    <Box sx={{ width: "100%", mt: 2 }}>
                      <LinearProgress className="linear-progress-red" variant="determinate" value={progressPercentage} />
                      <Typography variant="caption" textAlign="center" display="block" mt={1}>
                        {`${Math.round(progressPercentage)}%`}
                      </Typography>
                    </Box>
                  </Tooltip>

                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{display: 'flex', justifyContent: 'center'}}>
                    <StatisticsModal datasetDetails={row} />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{display: 'flex', justifyContent: 'center'}}>
                    <ConfigModal datasetId={row._id} />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{display: 'flex', justifyContent: 'center'}}>
                    <UninstallModal datasetId={row._id} status={row.status} handleUninstallConfirm={handleUninstallConfirm} />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{display: 'flex', justifyContent: 'center'}}>
                    <RemoveModal datasetId={row._id} status={row.status} handleRemoveConfirm={handleRemoveConfirm} />
                  </Box>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Box>
  );
};

export default DatasetPreparationTable;
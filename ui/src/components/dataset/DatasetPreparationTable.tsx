import React, { useEffect, useState } from 'react';
import { Box, IconButton, Modal, LinearProgress, Table, TableBody, TableCell, TableHead, TableRow, TableSortLabel, Typography, Tooltip } from '@mui/material'; 
import axios from '../../http/axiosConfig';
import DeleteIcon from '@mui/icons-material/Delete';
import CancelIcon from '@mui/icons-material/Cancel';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import DescriptionIcon from '@mui/icons-material/Description';
import '../../styles.css';
import ProgressDisplay from './ProgressDisplay';
import moment from 'moment';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { ConfirmationModal } from '../shared/ConfirmationModal';
import { TableTooltip } from '../shared/TableTooltip';

const FINISHED_STATUSES = ["DONE", "UNINSTALLED"]

type ActionModalProps = {
  datasetId: string;
  handleConfirm: (datasetId: string, setOpen: React.Dispatch<React.SetStateAction<boolean>>) => Promise<void>;
  icon: React.ElementType;
  title: string;
  disabledCondition: boolean;
  confirmationText: string;
  loaderText: string;
};

const ActionModal: React.FC<ActionModalProps> = ({ datasetId, handleConfirm, icon, title, disabledCondition, confirmationText, loaderText }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
    
  const handleConfirmClick = async () => {
    setLoading(true);
    await handleConfirm(datasetId, setOpen);
    setLoading(false);
  };
  
  return (
    <>
      <TableTooltip icon={icon} title={title} setOpen={setOpen} disabled={disabledCondition} />
      <ConfirmationModal text={confirmationText} open={open} onClose={() => setOpen(false)} loading={loading} loaderText={loaderText} handleClick={handleConfirmClick} />
    </>
  );
};

const StatisticsModal = (datasetDetails: any) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableTooltip icon={ShowChartIcon} title="Display more statistics" setOpen={setOpen} />
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
      <TableTooltip icon={DescriptionIcon} title="Display configuration json file" setOpen={setOpen} />
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
      const response = await axios.get('/api/dpr/displayDeployments');
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
                    return item; // If the deplyment isn't currently running, keep the item as is
                }

                const response = await axios.get(`/api/dpr/metrics`, { params: { id: item._id, name: item.name } });
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

            if (runningDatasets.length === 0) {
               // If there are no running datasets, don't overwrite datasets, just keep existing
                fetchListData();
            } else {
                // Update datasets with the new progress
                const updatedProgress = await Promise.all(promises);
                setDatasets(updatedProgress);
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    };

    if (datasets.length > 0) {
        fetchMetrics(); 
        const intervalId = setInterval(fetchMetrics, 30000); 
        return () => clearInterval(intervalId); 
    }
}, [currentlyRunningDatasets.length, datasets.length]); 


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
            const mongoData = row?.metrics?.mongodb || {}
            const progressData = Object.keys(mongoData).length > 0 ? mongoData.find((item: any) => item._id === 'progress_data') : null;
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
                    <ActionModal 
                      datasetId={row._id} 
                      handleConfirm={handleUninstallConfirm} 
                      icon={CancelIcon} 
                      title={FINISHED_STATUSES.includes(row.status) ? "Deployment has already been uninstalled" : "Trigger uninstall of the helm process"} 
                      disabledCondition={FINISHED_STATUSES.includes(row.status)} 
                      confirmationText="Are you sure you want to uninstall?" 
                      loaderText="Uninstalling..." 
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{display: 'flex', justifyContent: 'center'}}>
                    <ActionModal 
                      datasetId={row._id} 
                      handleConfirm={handleRemoveConfirm} 
                      icon={DeleteIcon} 
                      title={FINISHED_STATUSES.includes(row.status) ? "Remove this process from the table" : "You can't remove this row before the deployment is uninstalled"} 
                      disabledCondition={!FINISHED_STATUSES.includes(row.status)} 
                      confirmationText="Are you sure you want to remove this deployment from the table?" 
                      loaderText="Removing..." 
                    />
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
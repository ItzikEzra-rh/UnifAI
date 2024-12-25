import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, CircularProgress, IconButton, Modal, Typography, Checkbox } from '@mui/material';
import axios from '../../http/axiosConfig';
import ButtonGroup from '@mui/material/ButtonGroup';
import CollapseIcon from '@mui/icons-material/Remove';
import ExpandIcon from '@mui/icons-material/Add'; 
import VisibilityIcon from '@mui/icons-material/Visibility'; 
import FolderIcon from '@mui/icons-material/Folder';
import { SimpleTreeView, TreeItem } from '@mui/x-tree-view';  
import "./GitTree.css";

interface PropTypes {
  gitUrl: string;
  gitCredentialKey: string;
  gitBranchName: string;
  gitFolderPath: string;
  triggerOpen: boolean;
  checked: string[];
  setChecked: React.Dispatch<React.SetStateAction<string[]>>;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

interface TreeItemData {
  children?: TreeItemData[]; // Mark children as optional
  disabled: boolean;
  label: string | JSX.Element; // Allow JSX.Element for enhanced labels
  path: string;
  value: string;
}

interface TestItem {
  file: string;
  in_db: string;
}

interface TreeNodeProps {
  node: TreeItemData;
  checked: string[];
  setChecked: React.Dispatch<React.SetStateAction<string[]>>;
  setSelectedNodeLabel: (selectedNodeLabel: any) => void;
  setModalOpen: (modalOpen: boolean) => void;
  gitUrl: string;
  gitCredentialKey: string;
  gitFolderPath: string;
  gitBranchName: string;
}

export function stringContainsSpace(item: string) {
    return /\s/.test(item)
}

/**
 * create an hierarchical tree object which presents the files on stash (paths)
 * for each file checking if it is already in the database (dbList)
 * previousPath is used to accumulate the hierarchical path of file
 * @param paths
 * @param previousPath
 * @param dbList
 */
export function buildTree(paths: string[][], previousPath: string[] | string, dbList: {[key: string]: boolean}) {
  const items: any[] = [];
  paths.forEach(path => {
      const name = path[0];
      const value = path[0];
      const rest = path.slice(1);
      const isContainsSpace = stringContainsSpace(name);
      let item = items.find( e => e.name === name);
      
      if (item === undefined && value !== "") {
          const fileFullPath = previousPath + "/" + value;
          item = {
              name: name ,
              value: isContainsSpace ? fileFullPath + "_disabled" : fileFullPath,
              label: value,
              children: [],
              path: fileFullPath,
              disabled: isPathInDb(dbList, fileFullPath) || stringContainsSpace(name),
              className: isContainsSpace ? "warning_space" : "",
              title: isContainsSpace ? "Test name contains spaces, please remove any spaces from file name" : "",
              hasEyeIcon: true // Add this field to show the eye icon
          };
          items.push(item);
      }
      
      if (rest.length > 0) {
          item.children.push(rest);
      }
  });
  
  items.forEach(item =>  {
      item.children = buildTree(item.children, item.path, dbList);
      if (item.children.length === 0) {
          delete item["children"];
      }
  });
  return items;
}

/**
 * check if node is in dbList, keys in dbList are stored without "/" prefix
 * nodes have prefix "/" , we remove prefix to check if it's in the dictionary
 * @param dbList
 * @param node
 */
export function isPathInDb(dbList: {[key: string]: boolean}, node: string) {
    return dbList[node.substring(1)];
}

const TreeButtons: React.FC<{ collapse: () => void; expand: () => void }> = ({ collapse, expand }) => (
    <ButtonGroup variant="outlined" size="small">
      <Button title="collapse all" onClick={collapse} startIcon={<CollapseIcon />} />
      <Button title="expand all" onClick={expand} startIcon={<ExpandIcon />} />
    </ButtonGroup>
);

const TreeNode: React.FC<TreeNodeProps> = React.memo(({ 
                node, 
                checked, 
                setChecked, 
                setSelectedNodeLabel, 
                setModalOpen, 
                gitUrl, 
                gitCredentialKey, 
                gitFolderPath, 
                gitBranchName 
              }) => {
  const handleIconClick = () => {
    axios.get('/api/backend/fileContent', {
      params: {
        gitUrl,
        gitCredentialKey,
        gitFolderPath,
        gitBranchName,
        testPath: node.value
      }
    })
    .then((response) => {
      const { content, path } = response.data.result;
      console.log(`Test content for ${path}: \n${content}`);
      setSelectedNodeLabel(content); 
    })
    .catch((error) => {
      console.error('Error fetching test details:', error);
    });
    setSelectedNodeLabel(node.label); 
    setModalOpen(true);
  };

  const handleCheckboxChange = (node: TreeItemData, isChecked: boolean) => {
    const getAllChildren = (node: TreeItemData): string[] => {
      if (!node.children) return [node.value];
      return node.children.flatMap(getAllChildren).concat(node.value);
    };
  
    const childrenValues = getAllChildren(node);
  
    if (isChecked) {
      setChecked(prev => [...prev, ...childrenValues.filter((val) => !prev.includes(val))]);

    } else {
      setChecked((prev) => prev.filter((val) => !childrenValues.includes(val)));
    }
  };
  

  return (
    <TreeItem
      key={node.value}
      itemId={node.value}
      label={
        <Box sx={{
          height: '15px',
          display: 'flex',
          alignItems: 'center',
          padding: '2px 4px',
          fontSize: '0.875rem', 
        }}>
          <Checkbox
            checked={checked.includes(node.value)}
            disabled={node.disabled}
            onChange={(event) => handleCheckboxChange(node, event.target.checked)}
            sx={{ padding: '2px', marginRight: '4px' }} // Minimized padding and margin
            size="small"
          />
          {node.children?.length && node.children?.length > 0 ? 
            <FolderIcon sx={{ marginRight: 0.5, fontSize: '1rem' }} /> : 
            <IconButton onClick={handleIconClick} sx={{ marginRight: 1 }}>
              <VisibilityIcon fontSize='small'/>
            </IconButton>
          }
          {node.label}
        </Box>
      }
    >
      {node.children?.map((childNode) => (
        <TreeNode
          key={childNode.value}
          node={childNode}
          checked={checked}
          setChecked={setChecked}
          setSelectedNodeLabel={setSelectedNodeLabel}
          setModalOpen={setModalOpen}
          gitUrl={gitUrl}            
          gitCredentialKey={gitCredentialKey}
          gitFolderPath={gitFolderPath}
          gitBranchName={gitBranchName}
        />
      ))}
    </TreeItem>
  );
});


const GitForm: React.FC<PropTypes> = ({ gitUrl, gitCredentialKey, gitBranchName, gitFolderPath, triggerOpen, checked, setChecked, loading, setLoading }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [checkedDB, setCheckedDB] = useState<string[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedNodeLabel, setSelectedNodeLabel] = useState("");
  const [expanded, setExpanded] = useState<string[]>([]);
  const [nodes, setNodes] = useState<TreeItemData[]>([]);
  const [testsInDB, setTestsInDB] = useState<{ [key: string]: boolean }>({});

  const getTestsTree = useCallback(() => {
    setLoading(true);
    axios.get('/api/backend/files', {
      params: {
        gitUrl,
        gitCredentialKey,
        gitFolderPath,
        gitBranchName
      },
    }).then(response => buildTreeWrapper(response.data.result))
      .catch(() => setLoading(false));
  }, [gitUrl, gitCredentialKey]);


  const buildTreeWrapper = (testsList: TestItem[]) => {
    const paths: string[][] = [];
    const testsInDB: { [key: string]: boolean } = {};
    testsList.forEach(item => {
      paths.push(item.file.split('/'));
      testsInDB[item.file] = item.in_db === 'true';
    });
    const checkedDB = Object.keys(testsInDB)
      .filter(key => testsInDB[key])
      .map(e => `/${e}`);
    const nodes = buildTree(paths, '', testsInDB);
    setCheckedDB(checkedDB);
    setTestsInDB(testsInDB);
    setNodes(nodes);
    setLoading(false);
  };

  const open = () => {
    setLoading(true);
    setIsOpen(true);
    setExpanded([]);
    getTestsTree();
  };

  const close = () => {
    setIsOpen(false);
  };

  const collapseAll = () => setExpanded([]);
  const accumulatePath = (nodes: TreeItemData) => {
    let tmpArr: string[] = [];
    if (nodes.children && nodes.children.length > 0) {
      tmpArr = Array.prototype.concat(...nodes.children.map(child => accumulatePath(child)));
      tmpArr.push(nodes.value);
      return tmpArr;
    }
    return [nodes.value];
  };

  const expandAll = () => {
    setExpanded(Array.prototype.concat(...nodes.map(item => accumulatePath(item))));
  };

  useEffect(() => {
    if (triggerOpen) {
      open();
    }
  }, [triggerOpen]);

  const handleClose = () => {
    setModalOpen(false);
  };

  const countSelectedTests = (nodes: TreeItemData[], checked: string[]): number => {
    const countTests = (node: TreeItemData): number => {
      if (!node.children) return checked.includes(node.value) ? 1 : 0;
      return node.children.reduce((sum, child) => sum + countTests(child), 0);
    };
    return nodes.reduce((sum, node) => sum + countTests(node), 0);
  };
  
  return (
    <>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <CircularProgress sx={{ color: "red" }} />
        </div>
      ) : (
        <div className="form-section">
          <TreeButtons collapse={() => setExpanded([])} expand={expandAll} />
          <Box
    sx={{
      maxHeight: "400px", // Limit the height of the tree container
      overflow: "auto", // Enable scrolling when content overflows
      border: "1px solid #ccc", // Optional: Add a border for clarity
      borderRadius: "4px", // Optional: Rounded corners
    }}
  >
          <SimpleTreeView
  multiSelect
  selectedItems={checked}
  expandedItems={expanded}
  onExpandedItemsChange={(event, nodeIds) => setExpanded(nodeIds)}
>
  {nodes.map((node) => (
    <TreeNode 
      key={node.value} 
      node={node} 
      checked={checked} 
      setChecked={setChecked} 
      setSelectedNodeLabel={setSelectedNodeLabel} 
      setModalOpen={setModalOpen}
      gitUrl={gitUrl}            
      gitCredentialKey={gitCredentialKey}
      gitFolderPath={gitFolderPath}
      gitBranchName={gitBranchName}  
    />
  ))}
</SimpleTreeView>

          </Box>
          <div className="tests-selected">{countSelectedTests(nodes, checked)} Tests Selected</div>
          <Modal open={modalOpen} onClose={handleClose}>
            <Box
              sx={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: 300,
                bgcolor: "background.paper",
                boxShadow: 24,
                p: 4,
                borderRadius: "8px",
              }}
            >
              <Typography variant="h6" component="h2">
                {selectedNodeLabel}
              </Typography>
              <Typography sx={{ mt: 2 }}>content</Typography>
            </Box>
          </Modal>
        </div>
      )}
    </>
  );
};

export default GitForm;

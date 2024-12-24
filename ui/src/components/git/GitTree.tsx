import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, CircularProgress, IconButton, Modal, Typography, Checkbox } from '@mui/material';
import axios from '../../http/axiosConfig';
import ButtonGroup from '@mui/material/ButtonGroup';
import CollapseIcon from '@mui/icons-material/Remove'; // Replace with appropriate icon
import ExpandIcon from '@mui/icons-material/Add'; // Replace with appropriate icon
import VisibilityIcon from '@mui/icons-material/Visibility'; // Replace with appropriate icon
import { SimpleTreeView, TreeItem } from '@mui/x-tree-view';  // Updated import
import "./GitTree.css";
import FolderIcon from '@mui/icons-material/Folder'; // Folder icon for expandable nodes


interface PropTypes {
  gitUrl: string;
  gitCredentialKey: string;
  gitBranchName: string;
  gitFolderPath: string;
  triggerOpen: boolean;
  checked: string[];
  setChecked: (checked: string[]) => void;
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
  setChecked: (checked: string[]) => void;
  setSelectedNodeLabel: (selectedNodeLabel: any) => void;
  setModalOpen: (modalOpen: boolean) => void;
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

const TreeNode: React.FC<TreeNodeProps> = ({ node, checked, setChecked, setSelectedNodeLabel, setModalOpen }) => {
  const handleIconClick = () => {
    setSelectedNodeLabel(node.label); // Set the selected node label
    setModalOpen(true); // Open the modal
  };

  return (
    <TreeItem
      key={node.value}
      itemId={node.value}
      label={
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Checkbox
            checked={checked.includes(node.value)} // Check if node is selected
            disabled={node.disabled}
            onChange={(event) => {
              const newChecked = event.target.checked
                ? [...checked, node.value] // Add node to checked if selected
                : checked.filter((item) => item !== node.value); // Remove node if deselected
              setChecked(newChecked); // Update checked state
            }}
          />
          {node.children?.length && node.children?.length > 0 ? 
            <FolderIcon sx={{ marginRight: 1 }} /> : 
            <IconButton onClick={handleIconClick} sx={{ marginRight: 1 }}>
              <VisibilityIcon />
            </IconButton>
          }
          {node.label}
        </Box>
      }
    >
      {/* Recursively render children nodes */}
      {node.children?.map((childNode) => (
        <TreeNode
          key={childNode.value}
          node={childNode}
          checked={checked}
          setChecked={setChecked}
          setSelectedNodeLabel={setSelectedNodeLabel}
          setModalOpen={setModalOpen}
        />
      ))}
    </TreeItem>
  );
};


const GitForm: React.FC<PropTypes> = ({ gitUrl, gitCredentialKey, gitBranchName, gitFolderPath, triggerOpen, checked, setChecked, loading, setLoading }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState(false);
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

  const onClick = (node: any) => {
    console.log(node)
    setSelectedNodeLabel(node.value);
    setModalOpen(true);
  };

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

  return (
    <>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <CircularProgress sx={{ color: "red" }} />
        </div>
      ) : (
        <div className="form-section">
          <TreeButtons collapse={() => setExpanded([])} expand={expandAll} />
          <SimpleTreeView
            multiSelect
            selectedItems={checked}
            expandedItems={expanded}
            onExpandedItemsChange={(event, nodeIds) => setExpanded(nodeIds)}
          >
            {nodes.map((node) => (
              <TreeNode key={node.value} node={node} checked={checked} setChecked={setChecked} setSelectedNodeLabel={setSelectedNodeLabel} setModalOpen={setModalOpen}/>
            ))}
          </SimpleTreeView>
          <div className="tests-selected">{checked.length} Tests Selected</div>
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
                Node Label
              </Typography>
              <Typography sx={{ mt: 2 }}>{selectedNodeLabel}</Typography>
            </Box>
          </Modal>
        </div>
      )}
    </>
  );
};

export default GitForm;

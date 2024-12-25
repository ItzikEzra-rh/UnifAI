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
import SyntaxHighlighter from 'react-syntax-highlighter';
import { github } from 'react-syntax-highlighter/dist/esm/styles/hljs';

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
  testsCodeFramework: string;
}

interface TreeItemData {
  children?: TreeItemData[];
  disabled: boolean;
  label: string | JSX.Element;
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
  setSelectedNodeContent: (selectedNodeContent: any) => void;
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

/**
 * TreeNode Component
 * 
 * This component renders a single node in a hierarchical tree view. It supports both folder and file nodes. 
 * - For folder nodes, it displays a folder icon and allows expansion to show child nodes.
 * - For file nodes, it displays a visibility icon that, when clicked, fetches the content of the file via an API call and displays it in a modal.
 * 
 * It also includes a checkbox for selecting nodes. When checked, all descendant nodes (if any) are included in the `checked` state. 
 * The component is recursively rendered for child nodes, enabling deep tree structures.
 * 
 * Props:
 * - `node`: The data representing the current tree node, including label, value, and children.
 * - `checked`: Array of selected node values.
 * - `setChecked`: Function to update the selected nodes state.
 * - `setSelectedNodeLabel`: Function to set the label/content for the selected node in the modal.
 * - `setModalOpen`: Function to control the visibility of the modal.
 * - `gitUrl`: The URL of the Git repository.
 * - `gitCredentialKey`: Credential key for accessing the Git repository.
 * - `gitFolderPath`: Path to the folder within the Git repository.
 * - `gitBranchName`: The branch name in the Git repository.
 */

const TreeNode: React.FC<TreeNodeProps> = React.memo(({node, checked, setChecked, setSelectedNodeLabel, setSelectedNodeContent, setModalOpen, gitUrl, gitCredentialKey, gitFolderPath, gitBranchName}) => {
  const handleIconClick = () => {
    axios.get('/api/backend/fileContent', {params: {gitUrl, gitCredentialKey, gitFolderPath, gitBranchName, testPath: node.value}})
    .then((response) => {
      const { content, path } = response.data.result;
      setSelectedNodeContent(content); 
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
        <Box sx={{height: '15px', display: 'flex', alignItems: 'center', padding: '2px 4px', fontSize: '0.875rem'}}>
          <Checkbox
            checked={checked.includes(node.value)}
            disabled={node.disabled}
            onChange={(event) => handleCheckboxChange(node, event.target.checked)}
            sx={{ padding: '2px', marginRight: '4px' }}
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
          setSelectedNodeContent={setSelectedNodeContent}
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


const GitForm: React.FC<PropTypes> = ({ gitUrl, gitCredentialKey, gitBranchName, gitFolderPath, triggerOpen, checked, setChecked, loading, setLoading, testsCodeFramework }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [checkedDB, setCheckedDB] = useState<string[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedNodeLabel, setSelectedNodeLabel] = useState("");
  const [selectedNodeContent, setSelectedNodeContent] = useState("");
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
          <Box sx={{maxHeight: "400px", overflow: "auto", border: "1px solid #ccc", borderRadius: "4px"}}>
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
                  setSelectedNodeContent={setSelectedNodeContent}
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
                width: '80%',
                bgcolor: "background.paper",
                boxShadow: 24,
                p: 4,
                borderRadius: "8px",
              }}
            >
              <Typography variant="h4">{selectedNodeLabel}</Typography>
              {selectedNodeContent && (
                                  <div className="code-visualizer">
                                      <SyntaxHighlighter language={testsCodeFramework} style={github}>
                                          {selectedNodeContent}
                                      </SyntaxHighlighter>
                                  </div>)}
              
            </Box>
          </Modal>
        </div>
      )}
    </>
  );
};

export default GitForm;

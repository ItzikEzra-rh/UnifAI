import React, { useState, useEffect, useCallback } from 'react';
import { Button, CircularProgress, IconButton, Modal } from '@mui/material';
import axios from '../../http/axiosConfig';
import CheckboxTree from 'react-checkbox-tree';
import ButtonGroup from '@mui/material/ButtonGroup';
import CollapseIcon from '@mui/icons-material/Remove'; // Replace with appropriate icon
import ExpandIcon from '@mui/icons-material/Add'; // Replace with appropriate icon
import VisibilityIcon from '@mui/icons-material/Visibility'; // Replace with appropriate icon
import "./GitTree.css";

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

interface TreeItem {
  children: TreeItem[];
  disabled: boolean;
  label: string;
  path: string;
  value: string;
}

interface TestItem {
  file: string;
  in_db: string;
}

export function stringContainsSpace(item: string) {
    return /\s/.test(item)
}

/**
 * create an hierarchical tree object which present the files on stash (paths)
 * for each file checking if he already in database(dbList) if so he is disabled
 * previousPath is used accumulate the hierarchical path of file
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

const GitForm: React.FC<PropTypes> = ({ gitUrl, gitCredentialKey, gitBranchName, gitFolderPath, triggerOpen, checked, setChecked, loading, setLoading }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState(false);
  const [checkedDB, setCheckedDB] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<string[]>([]);
  const [nodes, setNodes] = useState<TreeItem[]>([]);
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
    const testPath = node.value
    console.log(testPath)
    setLoading(true);
    axios.get('/api/backend/fileContent', {
      params: {
        gitUrl,
        gitCredentialKey,
        gitFolderPath,
        gitBranchName,
        testPath
      }
    })
    .then(response => {
      console.log(response)
      const content = response.data.result.content;
      console.log(content)
      console.log(`Test Content:\n${content}`);
    })
    .catch(() => {
      console.error("Failed to fetch test content.");
    })
    .finally(() => {
      setLoading(false);
    });
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

  const onCheck = (checked: string[]) => {
    setChecked(checked.filter(item => !isPathInDb(testsInDB, item)));
  
    // // Fetch the test content for the clicked file path
    // checked.forEach(item => {
    //   if (!isPathInDb(testsInDB, item)) {
    //     fetchTestDetails(item); // Call fetchTestDetails with the path of the clicked item
    //   }
    // });
  };

  
  

//   const onResponse = (response: any) => {
//     if (response.error) {
//       getTestsTree();
//     } else {
//       close();
//     }
//   };

//   const onError = () => {
//     getTestsTree();
//   };

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
  const accumulatePath = (nodes: TreeItem) => {
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

  
const LabelTest = ( value: any ) => {
  const handleClick = () => {
    console.log(value);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <IconButton onClick={handleClick} title="View">
        <VisibilityIcon />
      </IconButton>
    </div>
  );
};

  return (
    <>
      {loading ?
      <div style={{ display: 'flex', justifyContent: 'center'}}>
        <CircularProgress sx={{color: "red",}} />
      </div> :
      <div className="form-section">
        <TreeButtons collapse={() => setExpanded([])} expand={expandAll} />
        <CheckboxTree nodes={nodes}
                      checked={checked}
                      expanded={expanded}
                      onCheck={(checkedItems) => setChecked(checkedItems)}
                      onExpand={(expandedItems) => setExpanded(expandedItems)}
        />
        <div className="tests-selected">{checked.length} Tests Selected</div>
      </div>}
    </>
  );
};

export default GitForm;

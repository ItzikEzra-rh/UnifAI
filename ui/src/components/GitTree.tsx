import React, { useState, useEffect, useCallback } from 'react';
import { Button, CircularProgress } from '@mui/material';
import axios from '../http/axiosConfig';
import CheckboxTree from 'react-checkbox-tree';
import ButtonGroup from '@mui/material/ButtonGroup';
import CollapseIcon from '@mui/icons-material/Remove'; // Replace with appropriate icon
import ExpandIcon from '@mui/icons-material/Add'; // Replace with appropriate icon
import "./GitTree.css";

interface PropTypes {
  gitUrl: string;
  gitCredentialKey: string;
  triggerOpen: boolean;
}

interface TreeItem {
  children: TreeItem[] | null;
  disabled: boolean | null;
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
export function buildTree (paths: string[][], previousPath: string[] | string, dbList: {[key: string]: boolean}) {
    const items = [];
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
                title: isContainsSpace ? "Test name contains spaces, please remove any spaces from file name" : ""
            };
            items.push(item);
        }
        if (rest.length > 0) {
            item.children.push(rest);
        }
    });
    items.forEach(item  =>  {
        item.children = buildTree(item.children, item.path, dbList);
        if (item.children.length === 0) {
            delete item["children"]
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

const GitForm: React.FC<PropTypes> = ({ gitUrl, gitCredentialKey, triggerOpen }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState<string[]>([]);
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
        gitFolderPath: '22.0',
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

  const onCheck = (checked: string[]) => {
    setChecked(checked.filter(item => !isPathInDb(testsInDB, item)));
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

  return (
    <>
        {loading ?
        <CircularProgress /> :
        <>
            <TreeButtons collapse={() => setExpanded([])} expand={() => setExpanded(nodes.map((item) => item.value))} />
            <CheckboxTree nodes={nodes}
                          checked={checked}
                          expanded={expanded}
                          onCheck={(checkedItems) => setChecked(checkedItems)}
                          onExpand={(expandedItems) => setExpanded(expandedItems)}
            />
            <div className="tests-selected">{checked.length} Tests Selected</div>
        </>}
    </>
  );
};

export default GitForm;

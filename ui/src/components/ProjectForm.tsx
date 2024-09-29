import React, { useEffect, useState } from 'react';
import { useForm, Controller, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import axios from '../http/axiosConfig';
import { FormData } from './types/constants'
import { TabPanel, FormField, FormDropdown, FormCheckbox, FormFileUpload } from './FormFields'
import { Box, Tabs, Tab, Button } from '@mui/material'; 
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import { github } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import GitForm from './GitTree';
import SuccessMessage from './SuccessMessage'
import '../styles.css';

SyntaxHighlighter.registerLanguage('python', python);

const schema = yup.object().shape({
    projectName: yup.string().required('Project Name is required'),
    trainingName: yup.string().required('Training Name is required'),
    gitUrl: yup.string().required('Git Repo Url is required'),
    gitCredentialKey: yup.string().required('Git Credential Key is required'),
    gitBranchName: yup.string().required('Git Branch Name is required'),
    gitFolderPath: yup.string(),
    // gitFolderPath: yup.string().required('Git Path to Expand From is required'),
    baseModelName: yup.string().oneOf(['Mistral', 'Lama', 'Granite']).required('Base Model Name is required'),
    testsCodeFramework: yup.string().oneOf(['Python', 'Robot', 'Go', 'Jmeter']).required('Tests Code Language is required'),
    numberOfTests: yup.number().required('Number of Tests is required').positive().integer(),
    expandDatasetTo: yup.string().oneOf(['5x', '10x', '25x', '50x', '100x']).required('Expand Dataset To is required'),
    datasetGradingUpgrade: yup.boolean(),
    // datasetGradingUpgrade: yup.boolean().required('Dataset Grading Upgrade is required'),
    parserFile: yup.mixed<FileList>().test('fileType', 'Only .py files are accepted', (value: FileList  | undefined) => {
      // Check if value is not null and is an instance of File
      if (value && value.length > 0) {
        // Check if the first file ends with .py
        return value[0].name.endsWith('.py');
      }
      return false;
    }).required('Parser File is required'),
});

const ProjectForm: React.FC = () => {
    const [activeTab, setActiveTab] = useState(0);
    const [uploadedCode, setUploadedCode] = useState<string | null>(null);
    const [triggerGitFormOpen, setTriggerGitFormOpen] = useState(false);
    const [isFirstTabValid, setIsFirstTabValid] = useState(false);
    const [isSecondTabValid, setIsSecondTabValid] = useState(false);
    const [isThirdTabValid, setIsThirdTabValid] = useState(false);
    const [formSubmitted, setFormSubmitted] = useState(false);

    // Existing state for checked items
    const [checked, setChecked] = useState<string[]>([]);

    const { control, handleSubmit, formState: { errors }, watch, setValue} = useForm<FormData>({
        resolver: yupResolver(schema),
        mode: 'onChange' // This will validate the form on every change,
    });

    const checkFirstTabValidity = (data: Array<string | null>): boolean => {
      const [projectName, trainingName, gitUrl, gitCredentialKey, gitBranchName, baseModelName, testsCodeFramework] = data;
      return (
        !!projectName && !!trainingName && !!gitUrl && !!gitCredentialKey && !!gitBranchName && !!baseModelName && !!testsCodeFramework
      );
    };

    const checkThirdTabValidity = (data: Array<string | FileList | null>): boolean => {
      const [expandDatasetTo, parserFile] = data;
      return (
        !!expandDatasetTo && !!parserFile
      );
    };

    const watchedFields = watch(['projectName', 'trainingName', 'gitUrl', 'gitCredentialKey', 'gitBranchName', 'baseModelName', 'testsCodeFramework']);
    const watchedFieldsThirdTab = watch(['expandDatasetTo', 'parserFile']);

    useEffect(() => {
      const [projectName, trainingName, gitUrl, gitCredentialKey, gitBranchName, baseModelName, testsCodeFramework] = watchedFields;
      setIsFirstTabValid(checkFirstTabValidity([projectName, trainingName, gitUrl, gitCredentialKey, gitBranchName, baseModelName, testsCodeFramework]));
    }, [watchedFields]);

    useEffect(() => {
      const [expandDatasetTo, parserFile] = watchedFieldsThirdTab;
      setIsThirdTabValid(checkThirdTabValidity([expandDatasetTo, parserFile]));
    }, [watchedFieldsThirdTab]);

    // Update the validity of the second tab when the checked items change
    useEffect(() => {
      setIsSecondTabValid(checked.length > 0);
    }, [checked]);

    const onSubmit: SubmitHandler<FormData> = async (data) => {
        try {
          const {projectName, trainingName, gitUrl, gitCredentialKey, gitFolderPath, gitBranchName, baseModelName, testsCodeFramework,
                 numberOfTests, expandDatasetTo, datasetGradingUpgrade, parserFile} = data;

          await axios.post('/api/backend/forms', {projectName, trainingName, gitUrl, gitCredentialKey, gitFolderPath, gitBranchName, baseModelName, testsCodeFramework,
            numberOfTests, expandDatasetTo, datasetGradingUpgrade});
          setFormSubmitted(true); // Set the state to true upon successful form submission
          console.log('Form submitted successfully:', data);
        } catch (error) {
          console.error('Error submitting form:', error);
        }
      };

    const handleNextClick = () => {
        if (activeTab === 0) {
          setTriggerGitFormOpen(true)
        }

        if (activeTab === 1) {
          setValue('numberOfTests', checked.length);
        }
        
        setActiveTab(activeTab + 1);
    };
    
    const handleTabChange = (event: React.ChangeEvent<{}>, newValue: number) => {
        setActiveTab(newValue);
    };

    const handleFileUpload = (files: FileList | null) => {
      if (files && files.length > 0) {
        setValue('parserFile', files);
        if (files && files[0]) {
          const reader = new FileReader();
          reader.onload = (e) => {
            const text = e.target?.result as string;
            setUploadedCode(text);
          };
          reader.readAsText(files[0]);
        }
      }
    };

    return (
        <Box className="form-container">
          {formSubmitted ? (<SuccessMessage />) : (
            <>
                <Tabs value={activeTab} onChange={handleTabChange} aria-label="form tabs" className="form-tabs">
                    <Tab label="Project Form" />
                    <Tab label="Git Form" className={activeTab == 1 || activeTab == 2 ? '' : 'disabled-tab'} />
                    <Tab label="Dataset Form" className={activeTab == 2 ? '' : 'disabled-tab'} />
                </Tabs>
                <TabPanel value={activeTab} index={0}>
                    <form className="form-section">
                    <FormField name="projectName" label="Project Name" control={control} errors={errors} />
                    <FormField name="trainingName" label="Training Name" control={control} errors={errors} />
                    <FormField name="gitUrl" label="Git Repository Url" control={control} errors={errors} />
                    <FormField name="gitCredentialKey" label="Git Credential Key" control={control} errors={errors} secret={true} />
                    <FormField name="gitBranchName" label="Git Branch Name" control={control} errors={errors} />
                    <FormField name="gitFolderPath" label="Git Path To Fetch From" control={control} errors={errors} />
                    <FormDropdown name="baseModelName" label="Foundational Model Name" control={control} errors={errors} options={['Mistral', 'Lama', 'Granite']} />
                    <FormDropdown name="testsCodeFramework" label="Tests Code Framework" control={control} errors={errors} options={['Python', 'Robot', 'Go', 'Jmeter']} />
                    <Button type="button" variant="contained" color="primary" onClick={handleNextClick} disabled={!isFirstTabValid} style={{ float: 'right', marginTop: '10px' }}>
                        Next
                    </Button>
                    </form>
                </TabPanel>
                <TabPanel value={activeTab} index={1}>
                  <GitForm gitUrl={watch('gitUrl')} gitCredentialKey={watch('gitCredentialKey')} gitBranchName={watch('gitBranchName')} gitFolderPath={watch('gitFolderPath') || ''} 
                          triggerOpen={triggerGitFormOpen} checked={checked} setChecked={setChecked}/>
                  <Button type="button" variant="contained" color="primary" onClick={handleNextClick} disabled={!isSecondTabValid} style={{ float: 'right', marginTop: '10px' }}>
                        Next
                  </Button>
                </TabPanel>
                <TabPanel value={activeTab} index={2}>
                    <form onSubmit={handleSubmit(onSubmit)} className="form-section">
                    <FormField name="numberOfTests" label="Number of Tests" type="number" control={control} errors={errors} disabled={true} />
                    <FormDropdown name="expandDatasetTo" label="Expand Dataset To" control={control} errors={errors} options={['5x', '10x', '25x', '50x', '100x']} />
                    <FormCheckbox name="datasetGradingUpgrade" label="Dataset Quality Upgrade" control={control} errors={errors} />
                    <FormFileUpload name="parserFile" label="Upload Parser File" control={control} errors={errors} onFileUpload={handleFileUpload} />
                    {uploadedCode && (
                        <div className="code-visualizer">
                            <SyntaxHighlighter language="python" style={github}>
                                {uploadedCode}
                            </SyntaxHighlighter>
                        </div>
                    )}
                    <Button type="submit" variant="contained" color="primary" disabled={!isThirdTabValid} style={{ float: 'right', marginTop: '10px' }}>
                        Create Dataset
                    </Button>
                    </form>
                </TabPanel>
            </>)}
        </Box>
      );
};

export default ProjectForm;

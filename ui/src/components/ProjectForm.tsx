import React, { useState } from 'react';
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
import '../styles.css';

SyntaxHighlighter.registerLanguage('python', python);

const schema = yup.object().shape({
    projectName: yup.string().required('Project Name is required'),
    trainingName: yup.string().required('Training Name is required'),
    gitPath: yup.string().required('Git Path to Expand From is required'),
    gitCredentialKey: yup.string().required('Git Credential Key is required'),
    baseModelName: yup.string().oneOf(['Mistarl', 'Lama']).required('Base Model Name is required'),
    testsCodeLanguage: yup.string().oneOf(['Python', 'Robot', 'Go', 'Jmeter']).required('Tests Code Language is required'),
    numberOfTests: yup.number().required('Number of Tests is required').positive().integer(),
    expandDatasetTo: yup.string().oneOf(['5x', '10x', '25x', '50x', '100x']).required('Expand Dataset To is required'),
    datasetGradingUpgrade: yup.boolean(),
    parserFile: yup.mixed().test('fileType', 'Only .py files are accepted', (value) => {
        return value && value[0] && value[0].name.endsWith('.py');
      }).required('Parser File is required'),
});

const ProjectForm: React.FC = () => {
    const [activeTab, setActiveTab] = useState(0);
    const [isSecondFormVisible, setIsSecondFormVisible] = useState(false);
    const [uploadedCode, setUploadedCode] = useState<string | null>(null);

    const { control, handleSubmit, formState: { errors }, watch} = useForm<FormData>({
        resolver: yupResolver(schema),
    });

    const onSubmit: SubmitHandler<FormData> = async (data) => {
        try {
          const formData = new FormData();
          Object.keys(data).forEach((key) => {
            formData.append(key, (data as any)[key]);
          });
          await axios.post('/api/forms', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
          console.log('Form submitted successfully:', data);
        } catch (error) {
          console.error('Error submitting form:', error);
        }
      };

    const handleNextClick = () => {
        setIsSecondFormVisible(true);
        setActiveTab(1);
    };
    
    const handleTabChange = (event: React.ChangeEvent<{}>, newValue: number) => {
        if (newValue === 1 && !isSecondFormVisible) {
          return;
        }
        setActiveTab(newValue);
    };

    const handleFileUpload = (files: FileList | null) => {
        if (files && files[0]) {
          const reader = new FileReader();
          reader.onload = (e) => {
            const text = e.target?.result as string;
            setUploadedCode(text);
          };
          reader.readAsText(files[0]);
        }
    };

    return (
        <Box className="form-container">
            <Tabs value={activeTab} onChange={handleTabChange} aria-label="form tabs" className="form-tabs">
                <Tab label="Initial Form" />
                <Tab label="Training Form" className={isSecondFormVisible ? '' : 'disabled-tab'} />
            </Tabs>
            <TabPanel value={activeTab} index={0}>
                <form className="form-section">
                <FormField name="projectName" label="Project Name" control={control} errors={errors} />
                <FormField name="trainingName" label="Training Name" control={control} errors={errors} />
                <FormField name="gitPath" label="Git Path to Fetch From" control={control} errors={errors} />
                <FormField name="gitCredentialKey" label="Git Credential Key" control={control} errors={errors} />
                <FormDropdown name="baseModelName" label="Base Model Name" control={control} errors={errors} options={['Mistarl', 'Lama']} />
                <FormDropdown name="testsCodeLanguage" label="Tests Code Language" control={control} errors={errors} options={['Python', 'Robot', 'Go', 'Jmeter']} />
                <Button type="button" variant="contained" color="primary" onClick={handleNextClick} style={{ float: 'right', marginTop: '10px' }}>
                    Next
                </Button>
                </form>
            </TabPanel>
            <TabPanel value={activeTab} index={1}>
                <form onSubmit={handleSubmit(onSubmit)} className="form-section">
                <FormField name="numberOfTests" label="Number of Tests" type="number" control={control} errors={errors} />
                <FormDropdown name="expandDatasetTo" label="Expand Dataset To" control={control} errors={errors} options={['5x', '10x', '25x', '50x', '100x']} />
                <FormCheckbox name="datasetGradingUpgrade" label="Dataset Grading Upgrade" control={control} errors={errors} />
                <FormFileUpload name="parserFile" label="Upload Parser File" control={control} errors={errors} onFileUpload={handleFileUpload} />
                {uploadedCode && (
                    <div className="code-visualizer">
                        <SyntaxHighlighter language="python" style={github}>
                            {uploadedCode}
                        </SyntaxHighlighter>
                    </div>
                )}
                <Button type="submit" variant="contained" color="primary" style={{ float: 'right', marginTop: '10px' }}>
                    Start Training
                </Button>
                </form>
            </TabPanel>
        </Box>
      );
};

export default ProjectForm;

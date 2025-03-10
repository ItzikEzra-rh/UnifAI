import React, { useEffect, useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import axios from '../../http/axiosConfig';
import { FormData } from '../types/constants'
import { FormField, FormDropdown, FormCheckbox, FormFileUpload } from '../shared/FormFields'
import { Box, Button, Step, StepContent, Stepper } from '@mui/material'; 
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import GitForm from '../git/GitTree';
import SuccessMessage from '../shared/SuccessMessage'
import '../../styles.css';
import { CustomStepIcon, CustomStepLabel } from '../shared/StepperIcons';

SyntaxHighlighter.registerLanguage('python', python);

const schema = yup.object().shape({
    projectName: yup.string().required('Project Name is required'),
    trainingName: yup.string().required('Training Name is required'),
    gitUrl: yup.string().required('Git Repo Url is required'),
    gitCredentialKey: yup.string().required('Git Credential Key is required'),
    gitBranchName: yup.string().required('Git Branch Name is required'),
    gitFolderPath: yup.string(),
    // gitFolderPath: yup.string().required('Git Path to Expand From is required'),
    baseModelName: yup.string().oneOf(['Mistral', 'Llama', 'Granite']).required('Base Model Name is required'),
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
    const [activeStep, setActiveStep] = useState(0);
    const [uploadedCode, setUploadedCode] = useState<string | null>(null);
    const [triggerGitFormOpen, setTriggerGitFormOpen] = useState(false);
    const [isFirstTabValid, setIsFirstTabValid] = useState(false);
    const [isSecondTabValid, setIsSecondTabValid] = useState(false);
    const [isThirdTabValid, setIsThirdTabValid] = useState(false);
    const [gitLoading, setGitLoading] = useState(false);
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

          await axios.post('/api/forms/insert', {projectName, trainingName, gitUrl, gitCredentialKey, gitFolderPath, gitBranchName, baseModelName, testsCodeFramework,
            numberOfTests, expandDatasetTo, datasetGradingUpgrade});
          setFormSubmitted(true); // Set the state to true upon successful form submission
          console.log('Form submitted successfully:', data);
        } catch (error) {
          console.error('Error submitting form:', error);
        }
      };

    const handleNextClick = () => {
        if (activeStep === 0) {
          setTriggerGitFormOpen(true)
        }

        if (activeStep === 1) {
          setValue('numberOfTests', checked.length);
        }
        
        setActiveStep(activeStep + 1);
    };

    const handleBackClick = () => {
      if (activeStep === 1) { // Reset the checked tests when going back to the first tab
        setChecked([]);
        setValue('numberOfTests', 0);
      }
      
      if (activeStep > 0) {
        setActiveStep((prev) => prev - 1);
      }
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
    <>     
    {formSubmitted ? 
      <SuccessMessage text="Form has been submitted, dataset generation will start soon" /> : 
      <Box className="form-container">
        <Stepper activeStep={activeStep} orientation="vertical">
          <Step>
            <CustomStepLabel StepIconComponent={(props) => <CustomStepIcon {...props} />}>
              Project Form
            </CustomStepLabel>
            <StepContent>
              <form className="form-section">
                <FormField name="projectName" label="Project Name" control={control} errors={errors} />
                <FormField name="trainingName" label="Training Name" control={control} errors={errors} />
                <FormField name="gitUrl" label="Git Repository Url" control={control} errors={errors} />
                <FormField name="gitCredentialKey" label="Git Credential Key" control={control} errors={errors} secret={true} />
                <FormField name="gitBranchName" label="Git Branch Name" control={control} errors={errors} />
                <FormField name="gitFolderPath" label="Git Path To Fetch From" control={control} errors={errors} />
                <FormDropdown name="baseModelName" label="Foundational Model Name" control={control} errors={errors} options={['Mistral', 'Llama', 'Granite']} />
                <FormDropdown name="testsCodeFramework" label="Tests Code Framework" control={control} errors={errors} options={['Python', 'Robot', 'Go', 'Jmeter']} />
                <div className="form-bottom-button">
                  <Button
                    type="button"
                    variant="contained"
                    className="end-button"
                    onClick={handleNextClick}
                    disabled={!isFirstTabValid}
                    style={{ width: '5%' }}
                  >
                    Next
                  </Button>
                </div>
              </form>
            </StepContent>
          </Step>
          <Step>
            <CustomStepLabel StepIconComponent={(props) => <CustomStepIcon {...props} />}>
              Git Form
            </CustomStepLabel>
            <StepContent>
              <div className="form-section">
                <GitForm projectFormDetails={{
                          gitUrl: watch('gitUrl'),
                          gitCredentialKey: watch('gitCredentialKey'),
                          gitBranchName: watch('gitBranchName'),
                          gitFolderPath: watch('gitFolderPath') || '',
                          testsCodeFramework: watch('testsCodeFramework'),
                        }} 
                        triggerOpen={triggerGitFormOpen} 
                        checked={checked} 
                        setChecked={setChecked} 
                        loading={gitLoading} 
                        setLoading={setGitLoading} />
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px'}}>
                  <Button type="button" variant="contained" className="end-button" onClick={handleBackClick}>
                    Back
                  </Button>
                  <Button type="button" variant="contained" className="end-button" onClick={handleNextClick} disabled={!isSecondTabValid || gitLoading} style={{ width: '5%', float: 'right',  }}>
                    Next
                  </Button>
                </div>
              </div>
            </StepContent>
          </Step>
          <Step>
            <CustomStepLabel StepIconComponent={(props) => <CustomStepIcon {...props} />}>
              Dataset Form
            </CustomStepLabel>
            <StepContent>
              <form onSubmit={handleSubmit(onSubmit)} className="form-section">
                <FormField name="numberOfTests" label="Number of Tests" type="number" control={control} errors={errors} disabled={true} />
                <FormDropdown name="expandDatasetTo" label="Expand Dataset To" control={control} errors={errors} options={['5x', '10x', '25x', '50x', '100x']} />
                <FormCheckbox name="datasetGradingUpgrade" label="Dataset Quality Upgrade" control={control} errors={errors} />
                <FormFileUpload name="parserFile" label="Upload Parser File" control={control} errors={errors} onFileUpload={handleFileUpload} />
                {uploadedCode && (
                  <SyntaxHighlighter className="code-visualizer" language="python" style={atomOneDark}>
                      {uploadedCode}
                  </SyntaxHighlighter>
                )}
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px'}}>
                  <Button type="button" variant="contained" className="end-button" onClick={handleBackClick}>
                    Back
                  </Button>
                  <Button type="submit" variant="contained" className="end-button" disabled={!isThirdTabValid} >
                      Create Dataset
                  </Button>
                </div>
              </form>
            </StepContent>
          </Step>
        </Stepper>
      </Box>}
    </>
    );
};

export default ProjectForm;

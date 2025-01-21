import React, { useEffect, useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import axios from '../../http/axiosConfig';
import axiosLLM from '../../http/axiosLLMConfig'
import { Box, Button, Stepper, StepContent, Step } from '@mui/material';
import { FormField, FormDropdown } from '../shared/FormFields';
import { CustomStepIcon, CustomStepLabel } from '../shared/StepperIcons';

type FormData = {
  projectName: string;
  trainingName: string;
  datasetName: string;
  epochNumber: number;
  saveSteps: number;
  warmupSteps: number;
};

interface RepoFileData {
  name: string;
}

const schema = yup.object().shape({
  projectName: yup.string().required('Project Name is required'),
  trainingName: yup.string().required('Training Name is required'),
  datasetName: yup.string().required('Dataset Name is required'),
  epochNumber: yup.number().required('Epoch Number is required').positive().integer(),
  saveSteps: yup.number().required('Save Steps is required').positive().integer(),
  warmupSteps: yup.number().required('Warmup Steps is required').positive().integer(),
});

const TrainingForm: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [forms, setForms] = useState<any[]>([]);
  const [data, setData] = useState<RepoFileData[]>([]);
  const [projects, setProjects] = useState<Set<string>>(new Set());
  const [trainingOptions, setTrainingOptions] = useState<string[]>([]);
  const { control, handleSubmit, watch, setValue, formState: { errors } } = useForm<FormData>({
    resolver: yupResolver(schema),
    mode: 'onChange',
  });

  const watchedProjectName = watch('projectName');

  useEffect(() => {
    const fetchForms = async () => {
      try {
        const response = await axios.get('/api/forms/retrieveForms');
        const forms = response.data.result;
        const projectSet = new Set<string>();
        forms.forEach((form: { projectName: string; trainingName: string }) => {
          projectSet.add(form.projectName);
        });
        setForms(forms);
        setProjects(projectSet);
      } catch (error) {
        console.error('Error fetching forms:', error);
      }
    };
    fetchForms();

    const fetchData = async () => {
      try {
        const response = await axiosLLM.get('/api/backend/getHfRepoFiles?repoId=oodeh/NcsRobotTestFramework&repoType=dataset');
        // Convert the array of file names to an array of objects with a 'name' property
        const transformedData = response.data.map((fileName: string) => ({ name: fileName }));
        setData(transformedData);
      } catch (error) {
        console.error('Error fetching repository files:', error);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (watchedProjectName) {
        const filteredTrainings = forms
            .filter((form: { projectName: string }) => form.projectName === watchedProjectName)
            .map((form: { trainingName: string }) => form.trainingName);
        setTrainingOptions(filteredTrainings);
    };
  }, [watchedProjectName]);

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    console.log('Form Submitted:', data);
  };

  const handleNextClick = () => {
    setActiveStep(activeStep + 1);
  };

  const handleBackClick = () => {
    if (activeStep > 0) {
      setActiveStep((prev) => prev - 1);
    }
  };

  const isTab1Valid = !!watch('projectName') && !!watch('trainingName') && !!watch('datasetName');
  const isTab2Valid = !!watch('epochNumber') && !!watch('saveSteps') && !!watch('warmupSteps');


  return (
    <Box className="form-container">
      <Stepper activeStep={activeStep} orientation="vertical">
        <Step>
          <CustomStepLabel StepIconComponent={(props) => <CustomStepIcon {...props} />}>
            Training Selection
          </CustomStepLabel>
          <StepContent>
            <Box className="form-section">
              <FormDropdown
                name="projectName"
                label="Choose Project"
                control={control}
                errors={errors}
                options={Array.from(projects)}
              />
              <FormDropdown
                name="trainingName"
                label="Choose Training Name"
                control={control}
                errors={errors}
                options={trainingOptions}
                disabled={!watch('projectName')}
              />
              <FormDropdown
                name="datasetName"
                label="Choose Dataset"
                control={control}
                errors={errors}
                options={data.map(dataset => dataset.name)}
                disabled={!watch('projectName')}
              />
              <div className="form-bottom-button">
                <Button type="button" variant="contained" className="end-button" onClick={handleNextClick} disabled={!isTab1Valid}>
                  Next
                </Button>
              </div>
            </Box>
          </StepContent>
        </Step>
        <Step>
          <CustomStepLabel StepIconComponent={(props) => <CustomStepIcon {...props} />}>
            Training Form
          </CustomStepLabel>
          <StepContent>
            <Box className="form-section">
              <form onSubmit={handleSubmit(onSubmit)}>
                <FormField name="epochNumber" label="Epoch Number" type="number" control={control} errors={errors} />
                <FormField name="saveSteps" label="Save Steps" type="number" control={control} errors={errors} />
                <FormField name="warmupSteps" label="Warmup Steps" type="number" control={control} errors={errors} />
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px'}}>
                  <Button type="button" variant="contained" className="end-button" onClick={handleBackClick} >
                    Back
                  </Button>
                  <Button type="submit" variant="contained" className="end-button" disabled={!isTab2Valid}>
                    Start Training
                  </Button>
                </div>
              </form>
            </Box>
          </StepContent>
        </Step>
      </Stepper>
    </Box>
  );
};

export default TrainingForm;

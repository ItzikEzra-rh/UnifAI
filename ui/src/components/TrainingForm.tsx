import React, { useEffect, useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import axios from '../http/axiosConfig';
import { Box, Tabs, Tab, Button } from '@mui/material';
import { FormField, FormDropdown } from './FormFields';

type FormData = {
  projectName: string;
  trainingName: string;
  epochNumber: number;
  saveSteps: number;
  warmupSteps: number;
};

const schema = yup.object().shape({
  projectName: yup.string().required('Project Name is required'),
  trainingName: yup.string().required('Training Name is required'),
  epochNumber: yup.number().required('Epoch Number is required').positive().integer(),
  saveSteps: yup.number().required('Save Steps is required').positive().integer(),
  warmupSteps: yup.number().required('Warmup Steps is required').positive().integer(),
});

const TrainingForm: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [forms, setForms] = useState<any[]>([]);
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
        const response = await axios.get('/api/backend/retrieveForms');
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
    setActiveTab(activeTab + 1);
  };

  const isTab1Valid = !!watch('projectName') && !!watch('trainingName');
  const isTab2Valid = !!watch('epochNumber') && !!watch('saveSteps') && !!watch('warmupSteps');

  return (
    <Box className="form-container">
      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} aria-label="form tabs" className="form-tabs">
        <Tab label="Training Selection" />
        <Tab label="Training Form" className={activeTab === 1 ? '' : 'disabled-tab'} />
      </Tabs>

      {activeTab === 0 && (
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
          <Button
            type="button"
            variant="contained"
            color="primary"
            onClick={handleNextClick}
            disabled={!isTab1Valid}
            style={{ float: 'right', marginTop: '10px' }}
          >
            Next
          </Button>
        </Box>
      )}

      {activeTab === 1 && (
        <Box className="form-section">
          <form onSubmit={handleSubmit(onSubmit)}>
            <FormField name="epochNumber" label="Epoch Number" type="number" control={control} errors={errors} />
            <FormField name="saveSteps" label="Save Steps" type="number" control={control} errors={errors} />
            <FormField name="warmupSteps" label="Warmup Steps" type="number" control={control} errors={errors} />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={!isTab2Valid}
              style={{ float: 'right', marginTop: '10px' }}
            >
              Start Training
            </Button>
          </form>
        </Box>
      )}
    </Box>
  );
};

export default TrainingForm;

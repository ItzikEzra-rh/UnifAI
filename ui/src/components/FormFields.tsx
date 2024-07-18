import { Button, TextField, MenuItem, FormControlLabel, Checkbox, Typography, Box } from '@mui/material';
import { Controller } from 'react-hook-form';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

interface FormFieldProps {
    name: keyof FormData;
    label: string;
    control: any;
    errors: any;
    type?: string;
}

interface FormDropdownProps {
    name: keyof FormData;
    label: string;
    control: any;
    errors: any;
    options: string[];
}

interface FormCheckboxProps {
    name: keyof FormData;
    label: string;
    control: any;
    errors: any;
}    

interface FormFileUploadProps {
    name: keyof FormData;
    label: string;
    control: any;
    errors: any;
    onFileUpload: (files: FileList | null) => void;
}

export const FormField: React.FC<FormFieldProps> = ({ name, label, control, errors, type = 'text' }) => (
    <div className="form-group">
        <label>{label}</label>
        <Controller
            name={name}
            control={control}
            render={({ field }) => <TextField {...field} type={type} fullWidth error={!!errors[name]} helperText={errors[name]?.message} />}
        />
    </div>
);

export const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box p={3}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
);


export const FormDropdown: React.FC<FormDropdownProps> = ({ name, label, control, errors, options }) => (
    <div className="form-group">
        <label>{label}</label>
        <Controller
            name={name}
            control={control}
            render={({ field }) => (
                <TextField
                {...field}
                select
                fullWidth
                error={!!errors[name]}
                helperText={errors[name]?.message}
                >
                {options.map((option) => (
                    <MenuItem key={option} value={option}>
                    {option}
                    </MenuItem>
                ))}
                </TextField>
            )}
        />
    </div>
);

export const FormCheckbox: React.FC<FormCheckboxProps> = ({ name, label, control, errors }) => (
    <div className="form-group">
        <Controller
            name={name}
            control={control}
            render={({ field }) => (
                <FormControlLabel
                control={<Checkbox {...field} checked={field.value} />}
                label={label}
            />)}
        />
    </div>
);


export const FormFileUpload: React.FC<FormFileUploadProps> = ({ name, label, control, errors, onFileUpload }) => (
    <div className="form-group">
      <label>{label}</label>
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <input
            type="file"
            accept=".py"
            onChange={(e) => {
              onFileUpload(e.target.files);
            }}
          />
        )}
      />
      {errors[name] && <Typography color="error">{errors[name]?.message}</Typography>}
    </div>
);
import React, { useEffect, useState } from 'react';
import { Box, Button } from '@mui/material';
import { SubmitHandler, useForm, } from 'react-hook-form';
import { FormFileUploadHelm } from '../shared/FormFields';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { LoadingOverlay } from '../shared/LoadingOverlay';

interface HelmJsonProps {
    onSubmit: SubmitHandler<any>;
    isLoading: boolean;
}

const UploadHelmJson: React.FC<HelmJsonProps> = ({ onSubmit, isLoading }) => {
    const [jsonDisplay, setJsonDisplay] = useState<string | null>(null);

    const { control, handleSubmit, setValue, formState: { errors }, reset } = useForm({
        defaultValues: {jsonFile: {}},
    });

    useEffect(() => {
        setJsonDisplay(null);
    }, []);

    const handleFileUpload = (files: FileList | null) => {
        if (files && files.length > 0) {
            const file = files[0]; 
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const jsonData = JSON.parse(e.target?.result as string);
                    setJsonDisplay(JSON.stringify(jsonData, null, 2)); 
                    setValue('jsonFile', jsonData);
                } catch (error) {
                    console.error('Invalid JSON file:', error);
                }
            };
            reader.readAsText(file);
        }
    };

    return (
        <>
        {isLoading ?
        (<LoadingOverlay text="Helm installation has been triggered." />) :
        (<Box className="form-container">
            <form className="form-section" onSubmit={handleSubmit(onSubmit)}>
                <FormFileUploadHelm
                    name="jsonFile"
                    label="Select a valid Json file"
                    control={control}
                    errors={errors} 
                    onFileUpload={handleFileUpload}
                    accept="application/json,.json"
                />
                {jsonDisplay && 
                    <SyntaxHighlighter className="code-visualizer" language="json" style={atomOneDark} >
                        {jsonDisplay}
                    </SyntaxHighlighter>
                }
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginTop: '10px' }}>
                    <Button type="submit" variant="contained" className="end-button" disabled={false}>
                        Install
                    </Button>
                </div>
            </form>
        </Box>)}
        </>
    );
};

export default UploadHelmJson;
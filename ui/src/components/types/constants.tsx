export interface FormData {
    projectName: string;
    trainingName: string;
    gitUrl: string;
    gitCredentialKey: string;
    gitFolderPath?: string;
    gitBranchName: string;
    testsCodeFramework: string;
    numberOfTests: number;
    datasetGradingUpgrade?: boolean;}

export interface TableFormData {
    projectName: string;
    trainingName: string;
    baseModelName: 'Mistral' | 'Llama' | 'Granite';
    testsCodeFramework: string;
    status: 'Initial' | 'In progress' | 'Finished';
    progress: string; // Represented by percentage (e.g., "50%")
    modelType: 'finetuned' | 'foundational' | 'checkpoint';
    checkpoint?: string;
}

export interface ModelData {
    modelId: string;
    modelName: string;
    hfRepoId: string;
    repoInternalLocation?: string; 
    trainingName: string;
    modelMaxSeqLen: number;
    modelType: string,
    project: string,
    checkpoint?: string,
    finetuneSteps?: any[], 
    promptTemplate?: {
        assistant_tag: string;
        end_tag: string;
        user_tag: string;
    };
    isRagEnabled?: boolean,
    isPackageSelectionRagEnabled?: boolean,
    // numTests: string,
    // dataSize: string,
}

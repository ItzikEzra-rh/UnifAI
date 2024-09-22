export interface FormData {
    projectName: string;
    trainingName: string;
    gitUrl: string;
    gitCredentialKey: string;
    gitFolderPath?: string;
    gitBranchName: string;
    baseModelName: 'Mistral' | 'Lama' | 'Granite';
    testsCodeFramework: 'Python' | 'Robot' | 'Go' | 'Jmeter';
    numberOfTests: number;
    expandDatasetTo: '5x' | '10x' | '25x' | '50x' | '100x';
    datasetGradingUpgrade?: boolean;
    parserFile: FileList;
}

export interface TableFormData {
    projectName: string;
    trainingName: string;
    baseModelName: 'Mistral' | 'Lama' | 'Granite';
    testsCodeFramework: 'Python' | 'Robot' | 'Go' | 'Jmeter';
    status: 'Initial' | 'In progress' | 'Finished';
    progress: string; // Represented by percentage (e.g., "50%")
    modelType: 'finetuned' | 'foundational' | 'checkpoint';
    checkpoint?: string;
}

export interface ModelData {
    modelId: string;
    modelName: string;
    trainingName: string;
    modelMaxSeqLen: number;
    modelType: string,
    project: string,
    checkpoint?: string,
    finetuneSteps?: any[], 
    // numTests: string,
    // dataSize: string,
}
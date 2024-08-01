export interface FormData {
    projectName: string;
    trainingName: string;
    gitUrl: string;
    gitCredentialKey: string;
    gitFolderPath?: string;
    gitBranchName: string;
    baseModelName: 'Mistarl' | 'Lama';
    testsCodeFramework: 'Python' | 'Robot' | 'Go' | 'Jmeter';
    numberOfTests: number;
    expandDatasetTo: '5x' | '10x' | '25x' | '50x' | '100x';
    datasetGradingUpgrade?: boolean;
    parserFile: FileList;
}

export interface TableFormData {
    projectName: string;
    trainingName: string;
    baseModelName: 'Mistarl' | 'Lama';
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
    dataSize: string,
    modelType: string,
    numTests: string,
    project: string,
    checkpoint?: string,
}
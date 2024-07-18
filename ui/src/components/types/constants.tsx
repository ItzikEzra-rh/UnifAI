export interface FormData {
    projectName: string;
    trainingName: string;
    gitPath: string;
    gitCredentialKey: string;
    baseModelName: 'Mistarl' | 'Lama';
    testsCodeFramework: 'Python' | 'Robot' | 'Go' | 'Jmeter';
    numberOfTests: number;
    expandDatasetTo: '5x' | '10x' | '25x' | '50x' | '100x';
    datasetGradingUpgrade: boolean;
    parserFile: FileList;
}

export interface TableFormData {
    projectName: string;
    trainingName: string;
    gitPath: string;
    gitCredentialKey: string;
    baseModelName: 'Mistarl' | 'Lama';
    testsCodeLanguage: 'Python' | 'Robot' | 'Go' | 'Jmeter';
    status: 'Initial' | 'Progress' | 'Finished';
    progress: string; // Represented by percentage (e.g., "50%")
}
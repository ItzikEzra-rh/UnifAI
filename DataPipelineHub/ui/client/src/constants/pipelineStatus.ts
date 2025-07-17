export const PIPELINE_STATUS = {
  PENDING: 'PENDING',
  ACTIVE: 'ACTIVE',
  DONE: 'DONE',
  ARCHIVED: 'ARCHIVED',
  FAILED: 'FAILED',
  PAUSED: 'PAUSED'
} as const;

export type PipelineStatus = typeof PIPELINE_STATUS[keyof typeof PIPELINE_STATUS];

export const PIPELINE_STATUS_VALUES = Object.values(PIPELINE_STATUS); 
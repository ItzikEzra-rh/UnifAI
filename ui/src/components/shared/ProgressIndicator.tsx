import React from 'react';

interface ProgressIndicatorProps {
  steps: string[];
  activeStep: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ steps, activeStep }) => {
  return (
    <div className="progress-indicator">
      {steps.map((step, index) => (
        <React.Fragment key={index}>
          <div className="progress-step-container">
            <div className={`progress-step ${activeStep >= index ? 'filled' : ''}`}>
              <div className="circle"></div>
            </div>
            <div className="label">{step}</div>
          </div>
          {index < steps.length - 1 && (
            <div className={`progress-line ${activeStep > index ? 'filled' : ''}`}></div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default ProgressIndicator;

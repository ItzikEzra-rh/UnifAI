import React from 'react';

interface ProgressIndicatorProps {
  steps: string[];
  activeStep: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ steps, activeStep }) => {
  return (
    <div className="progress-menu">
      <ul className="progress-list">
        {steps.map((step, index) => (
          <li
            key={index}
            className={`progress-item ${index < activeStep ? 'completed' : ''} ${index === activeStep ? 'active' : ''}`}
          >
            <div className="circle" />
            <div className="label">{step}</div>
            {index < steps.length - 1 && <div className="line"></div>}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ProgressIndicator;

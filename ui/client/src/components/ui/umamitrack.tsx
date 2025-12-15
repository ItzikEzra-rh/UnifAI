import React, { ReactElement, cloneElement } from 'react';
import { UmamiEvents, UmamiEventData } from '@/config/umamiEvents';

interface UmamiTrackProps {
  event: UmamiEvents | string;
  eventData?: UmamiEventData;
  children: ReactElement;
}

export const UmamiTrack: React.FC<UmamiTrackProps> = ({
  event,
  eventData,
  children,
}) => {
  // Build the umami props object
  const umamiProps: Record<string, string> = {
    'data-umami-event': event,
  };

  // Add event data as additional data attributes
  if (eventData) {
    Object.entries(eventData).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        // Convert camelCase to kebab-case for data attributes
        const kebabKey = key.replace(/([A-Z])/g, '-$1').toLowerCase();
        umamiProps[`data-umami-event-${kebabKey}`] = String(value);
      }
    });
  }

  // Clone the child element and add umami props
  return cloneElement(children, umamiProps);
};
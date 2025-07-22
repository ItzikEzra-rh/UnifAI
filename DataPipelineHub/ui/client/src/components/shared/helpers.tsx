import React from "react";
import { Bot, Settings } from 'lucide-react';

export const getIconComponent = (iconType: string) => {
  switch (iconType) {
    case 'bot':
      return React.createElement(Bot, { className: "w-4 h-4" });
    case 'settings':
      return React.createElement(Settings, { className: "w-4 h-4" });
    default:
      return React.createElement(Bot, { className: "w-4 h-4" });
  }
}; 
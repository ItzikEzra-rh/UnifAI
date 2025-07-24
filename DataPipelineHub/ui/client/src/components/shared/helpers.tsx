import React from "react";
import { Bot, Settings, MessagesSquare, FileText } from 'lucide-react';

export const getIconComponent = (iconType: string) => {
  switch (iconType) {
    case 'bot':
      return React.createElement(Bot, { className: "w-4 h-4" });
    case 'settings':
      return React.createElement(Settings, { className: "w-4 h-4" });
    case 'message-square':
      return React.createElement(MessagesSquare, { className: "w-4 h-4" });
    case 'file-text':
      return React.createElement(FileText, { className: "w-4 h-4" });
    default:
      return React.createElement(Bot, { className: "w-4 h-4" });
  }
}; 
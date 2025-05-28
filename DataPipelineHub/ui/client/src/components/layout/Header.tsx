import React from "react";
import { useState } from "react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { FaSearch, FaBell, FaQuestionCircle, FaPlus, FaBars, FaMoon, FaSun } from "react-icons/fa";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import SimpleTooltip from "@/components/shared/SimpleTooltip";
import { useTheme } from "@/contexts/ThemeContext";

interface HeaderProps {
  title: string;
  onToggleSidebar: () => void;
}

export default function Header({ title, onToggleSidebar }: HeaderProps) {
  const [hasNotifications] = useState(true);
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 bg-background-surface border-b border-gray-800 flex items-center justify-between px-6 py-2">
      <div className="flex items-center">
        <button 
          onClick={onToggleSidebar}
          className="mr-4 md:hidden text-gray-400 hover:text-gray-800 dark:hover:text-white"
        >
          <FaBars size={18} />
        </button>
        <motion.h1 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="font-heading font-bold text-xl text-white"
        >
          {title}
        </motion.h1>
      </div>
      <div className="flex items-center space-x-4">
        <SimpleTooltip content={<p>Search</p>}>
          <button className="p-2 rounded-full hover:bg-background-card text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors">
            <FaSearch />
          </button>
        </SimpleTooltip>
        
        <SimpleTooltip content={<p>Notifications</p>}>
          <button className="p-2 rounded-full hover:bg-background-card text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors relative">
            <FaBell />
            {hasNotifications && (
              <motion.span 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-1 right-1 w-2 h-2 rounded-full bg-accent"
              />
            )}
          </button>
        </SimpleTooltip>
        
        <SimpleTooltip content={<p>Help</p>}>
          <button className="p-2 rounded-full hover:bg-background-card text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors">
            <FaQuestionCircle />
          </button>
        </SimpleTooltip>
        
        <SimpleTooltip content={<p>{theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}</p>}>
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-full hover:bg-background-card text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors"
          >
            {theme === 'dark' ? <FaSun /> : <FaMoon />}
          </button>
        </SimpleTooltip>
        
        {/* <Button size="sm" className="ml-2 bg-primary hover:bg-opacity-80">
          <FaPlus className="mr-2 h-3 w-3" />
          <span>New Pipeline</span>
        </Button> */}
      </div>
    </header>
  );
}

import { pgTable, text, serial, integer, boolean, jsonb, timestamp, foreignKey } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User table
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  name: text("name").notNull(),
  email: text("email").notNull(),
  role: text("role").notNull().default("user"),
  avatar: text("avatar"),
  createdAt: timestamp("created_at").defaultNow(),
});

// Project table
export const projects = pgTable("projects", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  shortName: text("short_name").notNull(),
  icon: text("icon").notNull(),
  color: text("color").notNull(),
  isActive: boolean("is_active").default(false),
  processingPercentage: integer("processing_percentage").default(0),
  sources: integer("sources").default(0),
  documents: integer("documents").default(0),
  createdBy: integer("created_by").references(() => users.id),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Data source table
export const dataSources = pgTable("data_sources", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  type: text("type").notNull(), // jira, slack, document, github
  status: text("status").notNull(), // connected, disconnected, error
  config: jsonb("config").notNull(),
  projectId: integer("project_id").references(() => projects.id),
  lastSync: timestamp("last_sync"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Pipeline table
export const pipelines = pgTable("pipelines", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  status: text("status").notNull(), // processing, waiting, paused, completed, error
  progress: integer("progress").default(0),
  dataSourceId: integer("data_source_id").references(() => dataSources.id),
  projectId: integer("project_id").references(() => projects.id),
  config: jsonb("config").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Activity log table
export const activityLogs = pgTable("activity_logs", {
  id: serial("id").primaryKey(),
  type: text("type").notNull(), // success, error, info
  title: text("title").notNull(),
  description: text("description").notNull(),
  projectId: integer("project_id").references(() => projects.id),
  sourceType: text("source_type"),
  createdAt: timestamp("created_at").defaultNow(),
});

// Settings table
export const settings = pgTable("settings", {
  id: serial("id").primaryKey(),
  key: text("key").notNull().unique(),
  value: jsonb("value").notNull(),
  projectId: integer("project_id"),
});

// Insert schemas
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
  name: true,
  email: true,
  role: true,
  avatar: true,
});

export const insertProjectSchema = createInsertSchema(projects).pick({
  name: true,
  shortName: true,
  icon: true,
  color: true,
  isActive: true,
  processingPercentage: true,
  sources: true,
  documents: true,
  createdBy: true,
});

export const insertDataSourceSchema = createInsertSchema(dataSources).pick({
  name: true,
  type: true,
  status: true,
  config: true,
  projectId: true,
  lastSync: true,
});

export const insertPipelineSchema = createInsertSchema(pipelines).pick({
  name: true,
  status: true,
  progress: true,
  dataSourceId: true,
  projectId: true,
  config: true,
});

export const insertActivityLogSchema = createInsertSchema(activityLogs).pick({
  type: true,
  title: true,
  description: true,
  projectId: true,
  sourceType: true,
});

export const insertSettingsSchema = createInsertSchema(settings).pick({
  key: true,
  value: true,
  projectId: true,
});

// Types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type Project = typeof projects.$inferSelect;
export type InsertProject = z.infer<typeof insertProjectSchema>;

export type DataSource = typeof dataSources.$inferSelect;
export type InsertDataSource = z.infer<typeof insertDataSourceSchema>;

export type Pipeline = typeof pipelines.$inferSelect;
export type InsertPipeline = z.infer<typeof insertPipelineSchema>;

export type ActivityLog = typeof activityLogs.$inferSelect;
export type InsertActivityLog = z.infer<typeof insertActivityLogSchema>;

export type Setting = typeof settings.$inferSelect;
export type InsertSetting = z.infer<typeof insertSettingsSchema>;

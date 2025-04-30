import {
  User,
  InsertUser,
  users,
  Project,
  InsertProject,
  projects,
  DataSource,
  InsertDataSource,
  dataSources,
  Pipeline,
  InsertPipeline,
  pipelines,
  ActivityLog,
  InsertActivityLog,
  activityLogs,
  Setting,
  InsertSetting,
  settings,
} from "@shared/schema";

// Interface for storage methods
export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // Project methods
  getProjects(): Promise<Project[]>;
  getProject(id: number): Promise<Project | undefined>;
  createProject(project: InsertProject): Promise<Project>;
  updateProject(
    id: number,
    project: Partial<InsertProject>,
  ): Promise<Project | undefined>;
  deleteProject(id: number): Promise<boolean>;

  // Data source methods
  getDataSources(projectId?: number): Promise<DataSource[]>;
  getDataSource(id: number): Promise<DataSource | undefined>;
  createDataSource(dataSource: InsertDataSource): Promise<DataSource>;
  updateDataSource(
    id: number,
    dataSource: Partial<InsertDataSource>,
  ): Promise<DataSource | undefined>;
  deleteDataSource(id: number): Promise<boolean>;

  // Pipeline methods
  getPipelines(projectId?: number): Promise<Pipeline[]>;
  getPipeline(id: number): Promise<Pipeline | undefined>;
  createPipeline(pipeline: InsertPipeline): Promise<Pipeline>;
  updatePipeline(
    id: number,
    pipeline: Partial<InsertPipeline>,
  ): Promise<Pipeline | undefined>;
  deletePipeline(id: number): Promise<boolean>;

  // Activity log methods
  getActivityLogs(projectId?: number, limit?: number): Promise<ActivityLog[]>;
  createActivityLog(log: InsertActivityLog): Promise<ActivityLog>;

  // Settings methods
  getSetting(key: string, projectId?: number): Promise<Setting | undefined>;
  updateSetting(key: string, value: any, projectId?: number): Promise<Setting>;
}

// In-memory storage implementation
export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private projects: Map<number, Project>;
  private dataSources: Map<number, DataSource>;
  private pipelines: Map<number, Pipeline>;
  private activityLogs: Map<number, ActivityLog>;
  private settings: Map<string, Setting>;

  private userId = 1;
  private projectId = 1;
  private dataSourceId = 1;
  private pipelineId = 1;
  private activityLogId = 1;
  private settingId = 1;

  constructor() {
    this.users = new Map();
    this.projects = new Map();
    this.dataSources = new Map();
    this.pipelines = new Map();
    this.activityLogs = new Map();
    this.settings = new Map();

    // Initialize with sample data
    this.initializeSampleData();
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userId++;
    const user: User = { ...insertUser, id, createdAt: new Date() };
    this.users.set(id, user);
    return user;
  }

  // Project methods
  async getProjects(): Promise<Project[]> {
    return Array.from(this.projects.values());
  }

  async getProject(id: number): Promise<Project | undefined> {
    return this.projects.get(id);
  }

  async createProject(insertProject: InsertProject): Promise<Project> {
    const id = this.projectId++;
    const now = new Date();
    const project: Project = {
      ...insertProject,
      id,
      createdAt: now,
      updatedAt: now,
    };
    this.projects.set(id, project);
    return project;
  }

  async updateProject(
    id: number,
    projectData: Partial<InsertProject>,
  ): Promise<Project | undefined> {
    const project = this.projects.get(id);
    if (!project) return undefined;

    const updatedProject = {
      ...project,
      ...projectData,
      updatedAt: new Date(),
    };
    this.projects.set(id, updatedProject);
    return updatedProject;
  }

  async deleteProject(id: number): Promise<boolean> {
    return this.projects.delete(id);
  }

  // Data source methods
  async getDataSources(projectId?: number): Promise<DataSource[]> {
    const allDataSources = Array.from(this.dataSources.values());
    if (projectId === undefined) return allDataSources;
    return allDataSources.filter((ds) => ds.projectId === projectId);
  }

  async getDataSource(id: number): Promise<DataSource | undefined> {
    return this.dataSources.get(id);
  }

  async createDataSource(
    insertDataSource: InsertDataSource,
  ): Promise<DataSource> {
    const id = this.dataSourceId++;
    const now = new Date();
    const dataSource: DataSource = {
      ...insertDataSource,
      id,
      createdAt: now,
      updatedAt: now,
    };
    this.dataSources.set(id, dataSource);
    return dataSource;
  }

  async updateDataSource(
    id: number,
    dataSourceData: Partial<InsertDataSource>,
  ): Promise<DataSource | undefined> {
    const dataSource = this.dataSources.get(id);
    if (!dataSource) return undefined;

    const updatedDataSource = {
      ...dataSource,
      ...dataSourceData,
      updatedAt: new Date(),
    };
    this.dataSources.set(id, updatedDataSource);
    return updatedDataSource;
  }

  async deleteDataSource(id: number): Promise<boolean> {
    return this.dataSources.delete(id);
  }

  // Pipeline methods
  async getPipelines(projectId?: number): Promise<Pipeline[]> {
    const allPipelines = Array.from(this.pipelines.values());
    if (projectId === undefined) return allPipelines;
    return allPipelines.filter((p) => p.projectId === projectId);
  }

  async getPipeline(id: number): Promise<Pipeline | undefined> {
    return this.pipelines.get(id);
  }

  async createPipeline(insertPipeline: InsertPipeline): Promise<Pipeline> {
    const id = this.pipelineId++;
    const now = new Date();
    const pipeline: Pipeline = {
      ...insertPipeline,
      id,
      createdAt: now,
      updatedAt: now,
    };
    this.pipelines.set(id, pipeline);
    return pipeline;
  }

  async updatePipeline(
    id: number,
    pipelineData: Partial<InsertPipeline>,
  ): Promise<Pipeline | undefined> {
    const pipeline = this.pipelines.get(id);
    if (!pipeline) return undefined;

    const updatedPipeline = {
      ...pipeline,
      ...pipelineData,
      updatedAt: new Date(),
    };
    this.pipelines.set(id, updatedPipeline);
    return updatedPipeline;
  }

  async deletePipeline(id: number): Promise<boolean> {
    return this.pipelines.delete(id);
  }

  // Activity log methods
  async getActivityLogs(
    projectId?: number,
    limit: number = 10,
  ): Promise<ActivityLog[]> {
    const allLogs = Array.from(this.activityLogs.values()).sort(
      (a, b) => b.createdAt.getTime() - a.createdAt.getTime(),
    );

    if (projectId === undefined) return allLogs.slice(0, limit);
    return allLogs.filter((log) => log.projectId === projectId).slice(0, limit);
  }

  async createActivityLog(insertLog: InsertActivityLog): Promise<ActivityLog> {
    const id = this.activityLogId++;
    const log: ActivityLog = { ...insertLog, id, createdAt: new Date() };
    this.activityLogs.set(id, log);
    return log;
  }

  // Settings methods
  async getSetting(
    key: string,
    projectId?: number,
  ): Promise<Setting | undefined> {
    const settingKey = projectId ? `${key}-${projectId}` : key;
    return this.settings.get(settingKey);
  }

  async updateSetting(
    key: string,
    value: any,
    projectId?: number,
  ): Promise<Setting> {
    const settingKey = projectId ? `${key}-${projectId}` : key;
    const existingSetting = this.settings.get(settingKey);

    if (existingSetting) {
      const updatedSetting = { ...existingSetting, value };
      this.settings.set(settingKey, updatedSetting);
      return updatedSetting;
    } else {
      const id = this.settingId++;
      const newSetting: Setting = { id, key, value, projectId };
      this.settings.set(settingKey, newSetting);
      return newSetting;
    }
  }

  // Initialize with sample data
  private initializeSampleData() {
    // Create admin user
    const adminUser: InsertUser = {
      username: "admin",
      password: "admin123",
      name: "Alex Kim",
      email: "alex@example.com",
      role: "admin",
    };
    const user = this.createUser(adminUser);

    // Create projects
    const projectData = [
      {
        name: "Test Autmation Generator",
        shortName: "TAG",
        icon: "project",
        color: "primary",
        isActive: true,
        processingPercentage: 87,
        sources: 3,
        documents: 12,
        createdBy: 1,
      },
      {
        name: "AI Assistant",
        shortName: "AI",
        icon: "robot",
        color: "secondary",
        isActive: false,
        processingPercentage: 100,
        sources: 2,
        documents: 5,
        createdBy: 1,
      },
      {
        name: "Data Warehouse",
        shortName: "DW",
        icon: "database",
        color: "accent",
        isActive: false,
        processingPercentage: 62,
        sources: 1,
        documents: 9,
        createdBy: 1,
      },
    ];

    projectData.forEach(async (project) => {
      this.createProject(project);
    });

    // Create data sources
    const dataSourceData = [
      {
        name: "Jira Cloud",
        type: "jira",
        status: "connected",
        config: { url: "https://example.atlassian.net", project: "ENG" },
        projectId: 1,
        lastSync: new Date(Date.now() - 60 * 60 * 1000),
      },
      {
        name: "Engineering Slack",
        type: "slack",
        status: "connected",
        config: { workspace: "engineering", channels: ["general", "dev"] },
        projectId: 1,
        lastSync: new Date(Date.now() - 30 * 60 * 1000),
      },
      {
        name: "Documentation",
        type: "document",
        status: "connected",
        config: { path: "/docs", formats: ["pdf", "docx"] },
        projectId: 1,
        lastSync: new Date(Date.now() - 2 * 60 * 60 * 1000),
      },
      {
        name: "GitHub",
        type: "github",
        status: "disconnected",
        config: { repo: "dataflow/main" },
        projectId: 1,
      },
    ];

    dataSourceData.forEach(async (dataSource) => {
      this.createDataSource(dataSource);
    });

    // Create pipelines
    const pipelineData = [
      {
        name: "Jira Ticket Processing",
        status: "processing",
        progress: 85,
        dataSourceId: 1,
        projectId: 1,
        config: { extractFields: ["title", "description", "comments"] },
      },
      {
        name: "Slack Message Indexing",
        status: "waiting",
        progress: 0,
        dataSourceId: 2,
        projectId: 1,
        config: { includeThreads: true, timeRange: "30d" },
      },
      {
        name: "Document Extraction",
        status: "paused",
        progress: 45,
        dataSourceId: 3,
        projectId: 1,
        config: { extractTables: true, extractImages: false },
      },
    ];

    pipelineData.forEach(async (pipeline) => {
      this.createPipeline(pipeline);
    });

    // Create activity logs
    const activityLogData = [
      {
        type: "success",
        title: "Jira pipeline processing completed",
        description:
          "Successfully processed 230 Jira tickets from the Engineering board.",
        projectId: 1,
        sourceType: "jira",
      },
      {
        type: "error",
        title: "Slack connection error",
        description:
          "API rate limit exceeded when processing #general channel. Retrying in 15 minutes.",
        projectId: 2,
        sourceType: "slack",
      },
      {
        type: "info",
        title: "Document processing started",
        description:
          "Started processing 28 new PDF documents from shared drive.",
        projectId: 3,
        sourceType: "document",
      },
    ];

    activityLogData.forEach(async (log) => {
      this.createActivityLog(log);
    });

    // Create settings
    const settingsData = [
      { key: "darkMode", value: true },
      { key: "notifications", value: true },
      { key: "autoSyncInterval", value: 30 },
      { key: "embedModel", value: "text-embedding-3-large" },
      { key: "chunkSize", value: 512 },
      { key: "chunkOverlap", value: 50 },
    ];

    settingsData.forEach(async (setting) => {
      this.updateSetting(setting.key, setting.value);
    });
  }
}

export const storage = new MemStorage();

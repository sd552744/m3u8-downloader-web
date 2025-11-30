import axios from 'axios';
import { DownloadTask, SystemInfo, DownloadRequest } from '../types';

const API_BASE = '/api';   // 使用相对路径，nginx 会代理到后端

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export const taskApi = {
  createTask: async (taskData: DownloadRequest): Promise<DownloadTask> => {
    const response = await api.post('/tasks', taskData);
    return response.data;
  },

  getTasks: async (): Promise<DownloadTask[]> => {
    const response = await api.get('/tasks');
    return response.data;
  },

  getTask: async (taskId: string): Promise<DownloadTask> => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  pauseTask: async (taskId: string): Promise<void> => {
    await api.post(`/tasks/${taskId}/pause`);
  },

  resumeTask: async (taskId: string): Promise<void> => {
    await api.post(`/tasks/${taskId}/resume`);
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await api.delete(`/tasks/${taskId}`);
  },

  // 新增：还原任务接口
  restoreTask: async (taskId: string): Promise<void> => {
    await api.post(`/tasks/${taskId}/restore`);
  },
};

export const systemApi = {
  getInfo: async (): Promise<SystemInfo> => {
    const response = await api.get('/system/info');
    return response.data;
  },
};

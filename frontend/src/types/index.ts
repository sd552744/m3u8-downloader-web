export interface DownloadTask {
  task_id: string;
  url: string;
  filename: string;
  status: 'pending' | 'downloading' | 'completed' | 'paused' | 'failed';
  progress: number;
  file_size?: string;
  error_message?: string;
  created_at: string;
  max_threads: number;
  speed_limit?: number;
}

export interface SystemInfo {
  version: string;
  status: string;
  active_tasks: number;
  total_tasks: number;
  download_dir: string;
}

export interface DownloadRequest {
  url: string;
  filename: string;
  max_threads: number;
  speed_limit?: number;
  cookies?: string;
  quality_url?: string;
}

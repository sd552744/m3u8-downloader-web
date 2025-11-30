import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  Box,
  Typography,
  Alert,
} from '@mui/material';
import { DownloadRequest } from '../types';

interface TaskFormProps {
  onSubmit: (data: DownloadRequest) => Promise<void>;
  onClose: () => void;
}

const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, onClose }) => {
  const [formData, setFormData] = useState({
    url: '',
    filename: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 从设置中获取线程数
      const settings = localStorage.getItem('m3u8-downloader-settings');
      let max_threads = 10; // 默认10线程
      
      if (settings) {
        const parsedSettings = JSON.parse(settings);
        max_threads = parsedSettings.maxThreads || 10;
      }

      await onSubmit({
        url: formData.url,
        filename: formData.filename,
        max_threads: max_threads,
      });
      setFormData({
        url: '',
        filename: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '创建任务失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoName = () => {
    if (formData.url && !formData.filename) {
      try {
        const url = new URL(formData.url);
        const pathParts = url.pathname.split('/');
        const lastPart = pathParts[pathParts.length - 1];
        const name = lastPart.split('.')[0] || 'video';
        const timestamp = new Date().toLocaleTimeString('zh-CN', { 
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }).replace(/:/g, '');
        setFormData(prev => ({
          ...prev,
          filename: `${name}_${timestamp}.mp4`
        }));
      } catch {
        const timestamp = new Date().getTime();
        setFormData(prev => ({
          ...prev,
          filename: `video_${timestamp}.mp4`
        }));
      }
    }
  };

  return (
    <Dialog open={true} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📥 新建下载任务
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="M3U8 链接"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                required
                placeholder="输入 M3U8 链接"
                helperText="支持防盗链的M3U8链接，自动设置Referer和User-Agent"
              />
            </Grid>

            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="文件名"
                value={formData.filename}
                onChange={(e) => setFormData(prev => ({ ...prev, filename: e.target.value }))}
                required
                placeholder="输出文件名"
                helperText="建议使用 .mp4 作为文件扩展名"
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <Button
                fullWidth
                variant="outlined"
                onClick={handleAutoName}
                sx={{ height: '56px' }}
              >
                自动命名
              </Button>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary">
                💡 提示：线程数和并发任务数请在设置中配置全局参数
              </Typography>
              <Typography variant="body2" color="text.secondary">
                🎯 默认线程数: 10，最大线程数: 20
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ⚡ 默认并发任务数: 5，最大并发任务数: 10
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button 
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
        >
          {loading ? '创建中...' : '开始下载'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TaskForm;

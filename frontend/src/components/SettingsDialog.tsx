import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Divider,
  Alert,
  Grid,
} from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';
import { SystemInfo } from '../types';

interface Settings {
  maxThreads: number;
  maxConcurrentTasks: number;
}

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
  onClearCache: () => void;
  onUpdateConcurrency: (maxTasks: number) => void;
  systemInfo: SystemInfo | null;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({
  open,
  onClose,
  onClearCache,
  onUpdateConcurrency,
  systemInfo,
}) => {
  const [settings, setSettings] = useState<Settings>({
    maxThreads: 10,
    maxConcurrentTasks: 5,
  });

  const [message, setMessage] = useState('');

  useEffect(() => {
    const savedSettings = localStorage.getItem('m3u8-downloader-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('m3u8-downloader-settings', JSON.stringify(settings));
    
    // 更新并发任务数
    onUpdateConcurrency(settings.maxConcurrentTasks);
    
    setMessage('设置已保存并生效');
    setTimeout(() => setMessage(''), 3000);
  };

  const handleClearCache = () => {
    if (window.confirm('确定要清理所有缓存和下载文件吗？此操作不可撤销！')) {
      onClearCache();
      setMessage('缓存清理完成');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon />
          <Typography variant="h6">系统设置</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {message && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          {/* 下载设置 */}
          <Box>
            <Typography variant="h6" gutterBottom>
              下载设置
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>下载线程数</InputLabel>
                  <Select
                    value={settings.maxThreads}
                    label="下载线程数"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      maxThreads: e.target.value as number
                    }))}
                  >
                    <MenuItem value={1}>1 线程</MenuItem>
                    <MenuItem value={2}>2 线程</MenuItem>
                    <MenuItem value={4}>4 线程</MenuItem>
                    <MenuItem value={8}>8 线程</MenuItem>
                    <MenuItem value={10}>10 线程 (推荐)</MenuItem>
                    <MenuItem value={16}>16 线程</MenuItem>
                    <MenuItem value={20}>20 线程 (最大)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>并发任务数</InputLabel>
                  <Select
                    value={settings.maxConcurrentTasks}
                    label="并发任务数"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      maxConcurrentTasks: e.target.value as number
                    }))}
                  >
                    <MenuItem value={1}>1 个任务</MenuItem>
                    <MenuItem value={2}>2 个任务</MenuItem>
                    <MenuItem value={3}>3 个任务</MenuItem>
                    <MenuItem value={5}>5 个任务 (推荐)</MenuItem>
                    <MenuItem value={8}>8 个任务</MenuItem>
                    <MenuItem value={10}>10 个任务 (最大)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* 系统信息 */}
          {systemInfo && (
            <Box>
              <Typography variant="h6" gutterBottom>
                系统状态
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    磁盘使用: {systemInfo.disk_usage}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    文件数量: {systemInfo.file_count}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}

          <Divider />

          {/* 缓存管理 */}
          <Box>
            <Typography variant="h6" gutterBottom>
              缓存管理
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              清理所有下载缓存和已完成文件
            </Typography>
            <Button
              variant="outlined"
              color="warning"
              onClick={handleClearCache}
              fullWidth
            >
              清理所有缓存和文件
            </Button>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSave} variant="contained">
          保存设置
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog;

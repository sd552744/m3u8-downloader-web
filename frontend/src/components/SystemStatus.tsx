import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle,
  Download,
  Storage,
  Speed,
} from '@mui/icons-material';
import { SystemInfo } from '../types';

interface SystemStatusProps {
  info: SystemInfo | null;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ info }) => {
  if (!info) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography>加载系统信息中...</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, mb: 2, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.100' }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <Chip
          icon={<CheckCircle />}
          label={`系统状态: ${info.status === 'running' ? '运行中' : '停止'}`}
          color={info.status === 'running' ? 'success' : 'error'}
          variant="outlined"
        />
        
        <Chip
          icon={<Storage />}
          label={`磁盘使用: ${info.disk_usage}`}
          variant="outlined"
        />
        
        <Chip
          icon={<Download />}
          label={`文件数量: ${info.file_count}`}
          variant="outlined"
        />
        
        <Chip
          icon={<Speed />}
          label={`版本: ${info.version}`}
          variant="outlined"
        />
        
        <Box sx={{ flexGrow: 1 }} />
        
        <Typography variant="body2" color="text.secondary">
          下载目录: {info.download_dir}
        </Typography>
      </Box>
    </Paper>
  );
};

export default SystemStatus;

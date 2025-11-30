import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  LinearProgress,
  Chip,
  Typography,
  Box,
} from '@mui/material';
import { PlayArrow, Pause, Delete, Download } from '@mui/icons-material';
import { DownloadTask } from '../types';

interface TaskListProps {
  tasks: DownloadTask[];
  onPause: (taskId: string) => void;
  onResume: (taskId: string) => void;
  onDelete: (taskId: string) => void;
  onDownload: (taskId: string, filename: string) => void;
}

const TaskList: React.FC<TaskListProps> = ({ 
  tasks, 
  onPause, 
  onResume, 
  onDelete, 
  onDownload 
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'downloading': return 'primary';
      case 'paused': return 'warning';
      case 'failed': return 'error';
      case 'queued': return 'default';
      case 'pending': return 'info';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'downloading': return '下载中';
      case 'completed': return '已完成';
      case 'paused': return '已暂停';
      case 'failed': return '失败';
      case 'pending': return '等待中';
      case 'queued': return '排队中';
      case 'deleted': return '已删除';
      default: return status;
    }
  };

  if (tasks.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="textSecondary">
          暂无下载任务
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>文件名</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>进度</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.task_id}>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ mb: 0.5 }}>
                    {task.filename}
                  </Typography>
                  {task.file_size && (
                    <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                      大小: {task.file_size}
                    </Typography>
                  )}
                  {task.download_speed && task.status === 'downloading' && (
                    <Typography variant="caption" color="primary" sx={{ display: 'block' }}>
                      速度: {task.download_speed}
                    </Typography>
                  )}
                  {task.error_message && (
                    <Typography variant="caption" color="error" sx={{ display: 'block' }}>
                      错误: {task.error_message}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Chip
                    label={getStatusText(task.status)}
                    color={getStatusColor(task.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: '100%' }}>
                      <LinearProgress
                        variant="determinate"
                        value={task.progress}
                        sx={{ 
                          height: 8, 
                          borderRadius: 4,
                          backgroundColor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: 
                              task.status === 'completed' ? 'success.main' :
                              task.status === 'failed' ? 'error.main' :
                              task.status === 'paused' ? 'warning.main' :
                              'primary.main'
                          }
                        }}
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary" sx={{ minWidth: 40 }}>
                      {Math.round(task.progress)}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {/* 下载按钮 - 只在完成状态显示 */}
                    {task.status === 'completed' && (
                      <IconButton 
                        size="small" 
                        onClick={() => onDownload(task.task_id, task.filename)}
                        title="下载文件"
                        color="primary"
                      >
                        <Download />
                      </IconButton>
                    )}
                    
                    {/* 暂停/继续按钮 */}
                    {task.status === 'downloading' && (
                      <IconButton
                        size="small"
                        onClick={() => onPause(task.task_id)}
                        title="暂停"
                        color="primary"
                      >
                        <Pause />
                      </IconButton>
                    )}
                    {task.status === 'paused' && (
                      <IconButton
                        size="small"
                        onClick={() => onResume(task.task_id)}
                        title="继续"
                        color="primary"
                      >
                        <PlayArrow />
                      </IconButton>
                    )}
                    
                    {/* 删除按钮 */}
                    <IconButton
                      size="small"
                      onClick={() => onDelete(task.task_id)}
                      title="删除任务"
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default TaskList;

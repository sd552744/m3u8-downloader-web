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
  Chip,
  Typography,
  Box,
} from '@mui/material';
import { Download, Delete } from '@mui/icons-material';
import { DownloadTask } from '../types';

interface CompletedTasksProps {
  tasks: DownloadTask[];
  onDownload: (taskId: string, filename: string) => void;
  onDelete: (taskId: string) => void;
}

const CompletedTasks: React.FC<CompletedTasksProps> = ({ 
  tasks, 
  onDownload, 
  onDelete 
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  if (tasks.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="textSecondary">
          暂无已完成的任务
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
              <TableCell>大小</TableCell>
              <TableCell>完成时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.task_id}>
                <TableCell>
                  <Typography variant="body2" noWrap>
                    {task.filename}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={task.file_size || '未知'}
                    color="success"
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="textSecondary">
                    {formatDate(task.created_at)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton 
                      size="small" 
                      onClick={() => onDownload(task.task_id, task.filename)}
                      title="下载文件"
                      color="primary"
                    >
                      <Download />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => onDelete(task.task_id)}
                      title="删除文件"
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

export default CompletedTasks;

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
  Button,
} from '@mui/material';
import { Restore, DeleteForever } from '@mui/icons-material';
import { DownloadTask } from '../types';

interface RecycleBinProps {
  tasks: DownloadTask[];
  onRestore: (taskId: string) => void;
  onPermanentDelete: (taskId: string) => void;
  onEmptyRecycleBin: () => void;
}

const RecycleBin: React.FC<RecycleBinProps> = ({ 
  tasks, 
  onRestore, 
  onPermanentDelete,
  onEmptyRecycleBin 
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  if (tasks.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="textSecondary">
          回收站为空
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>文件名</TableCell>
                <TableCell>大小</TableCell>
                <TableCell>删除时间</TableCell>
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
                      color="default"
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
                        onClick={() => onRestore(task.task_id)}
                        title="还原文件"
                        color="primary"
                      >
                        <Restore />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => onPermanentDelete(task.task_id)}
                        title="永久删除"
                        color="error"
                      >
                        <DeleteForever />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default RecycleBin;

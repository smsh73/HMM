import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Grid,
  LinearProgress,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const PerformancePage: React.FC = () => {
  const { user } = useAuth();
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { data: systemResources, isLoading: loadingSystem, refetch: refetchSystem } = useQuery({
    queryKey: ['system-resources'],
    queryFn: async () => {
      const response = await api.get('/performance/system');
      return response.data;
    },
    refetchInterval: autoRefresh ? 5000 : false,
  });

  const { data: processResources, isLoading: loadingProcess, refetch: refetchProcess } = useQuery({
    queryKey: ['process-resources'],
    queryFn: async () => {
      const response = await api.get('/performance/process');
      return response.data;
    },
    refetchInterval: autoRefresh ? 5000 : false,
  });

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        성능 모니터링 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">성능 모니터링</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            refetchSystem();
            refetchProcess();
          }}
        >
          새로고침
        </Button>
      </Box>

      {loadingSystem || loadingProcess ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* 시스템 리소스 */}
          {systemResources && !systemResources.error && (
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      CPU 사용률
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={systemResources.cpu?.percent || 0}
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                      </Box>
                      <Typography variant="h6">
                        {systemResources.cpu?.percent?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      코어 수: {systemResources.cpu?.count || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      메모리 사용률
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={systemResources.memory?.percent || 0}
                          sx={{ height: 10, borderRadius: 5 }}
                          color={
                            (systemResources.memory?.percent || 0) > 80
                              ? 'error'
                              : (systemResources.memory?.percent || 0) > 60
                              ? 'warning'
                              : 'primary'
                          }
                        />
                      </Box>
                      <Typography variant="h6">
                        {systemResources.memory?.percent?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      사용: {formatBytes(systemResources.memory?.used || 0)} /{' '}
                      {formatBytes(systemResources.memory?.total || 0)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      디스크 사용률
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={systemResources.disk?.percent || 0}
                          sx={{ height: 10, borderRadius: 5 }}
                          color={
                            (systemResources.disk?.percent || 0) > 80
                              ? 'error'
                              : (systemResources.disk?.percent || 0) > 60
                              ? 'warning'
                              : 'primary'
                          }
                        />
                      </Box>
                      <Typography variant="h6">
                        {systemResources.disk?.percent?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      사용: {formatBytes(systemResources.disk?.used || 0)} /{' '}
                      {formatBytes(systemResources.disk?.total || 0)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* 프로세스 리소스 */}
          {processResources && !processResources.error && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                프로세스 리소스
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>항목</TableCell>
                      <TableCell>값</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>프로세스 ID</TableCell>
                      <TableCell>{processResources.pid}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>CPU 사용률</TableCell>
                      <TableCell>
                        {processResources.cpu_percent?.toFixed(2) || 0}%
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>물리 메모리 (RSS)</TableCell>
                      <TableCell>
                        {formatBytes(processResources.memory?.rss || 0)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>가상 메모리 (VMS)</TableCell>
                      <TableCell>
                        {formatBytes(processResources.memory?.vms || 0)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>스레드 수</TableCell>
                      <TableCell>{processResources.num_threads || 0}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>열린 파일 수</TableCell>
                      <TableCell>{processResources.open_files || 0}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {(systemResources?.error || processResources?.error) && (
            <Alert severity="error" sx={{ mt: 2 }}>
              리소스 정보를 가져올 수 없습니다.
            </Alert>
          )}
        </>
      )}
    </Box>
  );
};

export default PerformancePage;

import React, { useState } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import { Download as DownloadIcon, Delete as DeleteIcon, PlayArrow as PlayIcon, Stop as StopIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import HuggingFaceModelsPage from './HuggingFaceModelsPage';

const ModelManagementPage: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const queryClient = useQueryClient();

  const { data: availableModels, isLoading: loadingAvailable } = useQuery({
    queryKey: ['available-models'],
    queryFn: async () => {
      const response = await api.get('/models/available');
      return response.data.models;
    },
  });

  const { data: localModels, isLoading: loadingLocal } = useQuery({
    queryKey: ['local-models'],
    queryFn: async () => {
      const response = await api.get('/models/local');
      return response.data.models;
    },
  });

  const downloadMutation = useMutation({
    mutationFn: async (modelName: string) => {
      await api.post(`/models/download/${modelName}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['local-models'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (modelId: string) => {
      await api.delete(`/models/${modelId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['local-models'] });
    },
  });

  const { data: servingStatus } = useQuery({
    queryKey: ['serving-status'],
    queryFn: async () => {
      const response = await api.get('/serving/status');
      return response.data.models;
    },
    refetchInterval: 5000, // 5초마다 상태 갱신
  });

  const startServingMutation = useMutation({
    mutationFn: async (modelId: string) => {
      await api.post('/serving/start', {
        model_id: modelId,
        model_type: 'ollama',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serving-status'] });
    },
  });

  const stopServingMutation = useMutation({
    mutationFn: async (modelId: string) => {
      await api.post(`/serving/stop/${modelId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serving-status'] });
    },
  });

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        모델 관리 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        모델 관리
      </Typography>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="로컬 모델" />
        <Tab label="Hugging Face" />
        <Tab label="서빙 상태" />
      </Tabs>

      {tabValue === 0 && (
        <>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          다운로드된 모델
        </Typography>
        {loadingLocal ? (
          <CircularProgress />
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>모델명</TableCell>
                  <TableCell>타입</TableCell>
                  <TableCell>상태</TableCell>
                  <TableCell>다운로드 진행률</TableCell>
                  <TableCell>작업</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {localModels?.map((model: any) => (
                  <TableRow key={model.id}>
                    <TableCell>{model.model_name}</TableCell>
                    <TableCell>{model.model_type}</TableCell>
                    <TableCell>
                      <Chip
                        label={model.is_downloaded ? '다운로드 완료' : '다운로드 중'}
                        color={model.is_downloaded ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ width: '100%' }}>
                        <LinearProgress
                          variant="determinate"
                          value={model.download_progress}
                        />
                        <Typography variant="caption">
                          {model.download_progress}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => {
                          if (window.confirm('정말 삭제하시겠습니까?')) {
                            deleteMutation.mutate(model.id);
                          }
                        }}
                      >
                        삭제
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          사용 가능한 모델 (Ollama)
        </Typography>
        {loadingAvailable ? (
          <CircularProgress />
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>모델명</TableCell>
                  <TableCell>크기</TableCell>
                  <TableCell>작업</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {availableModels?.map((model: any, idx: number) => (
                  <TableRow key={idx}>
                    <TableCell>{model.name}</TableCell>
                    <TableCell>
                      {(model.size / 1024 / 1024 / 1024).toFixed(2)} GB
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<DownloadIcon />}
                        onClick={() => downloadMutation.mutate(model.name)}
                        disabled={downloadMutation.isPending}
                      >
                        다운로드
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
      </>
      )}

      {tabValue === 1 && <HuggingFaceModelsPage />}

      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            서빙 중인 모델
          </Typography>
          {servingStatus && servingStatus.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>모델 ID</TableCell>
                    <TableCell>타입</TableCell>
                    <TableCell>상태</TableCell>
                    <TableCell>작업</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {servingStatus.map((model: any, idx: number) => (
                    <TableRow key={idx}>
                      <TableCell>{model.model_id}</TableCell>
                      <TableCell>{model.model_type}</TableCell>
                      <TableCell>
                        <Chip
                          label={model.status}
                          color={model.status === 'running' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<StopIcon />}
                          onClick={() => stopServingMutation.mutate(model.model_id)}
                        >
                          중지
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography color="text.secondary">
              서빙 중인 모델이 없습니다.
            </Typography>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default ModelManagementPage;


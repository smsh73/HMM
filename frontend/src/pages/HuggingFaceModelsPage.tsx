import React, { useState } from 'react';
import {
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import { Search as SearchIcon, Download as DownloadIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const HuggingFaceModelsPage: React.FC = () => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [task, setTask] = useState('');
  const [library, setLibrary] = useState('');
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: models, isLoading, refetch } = useQuery({
    queryKey: ['hf-models', searchQuery, task, library],
    queryFn: async () => {
      const params: any = { limit: 50 };
      if (searchQuery) params.q = searchQuery;
      if (task) params.task = task;
      if (library) params.library = library;
      
      const response = await api.get('/huggingface/models/search', { params });
      return response.data.models;
    },
    enabled: false, // 수동 검색
  });

  const downloadMutation = useMutation({
    mutationFn: async (modelId: string) => {
      await api.post(`/huggingface/models/${modelId}/download`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['local-models'] });
      setDownloadDialogOpen(false);
    },
  });

  const handleSearch = () => {
    refetch();
  };

  const handleDownload = (model: any) => {
    setSelectedModel(model);
    setDownloadDialogOpen(true);
  };

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        Hugging Face 모델 관리 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Hugging Face 모델 브라우징
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            label="검색어"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="모델명 또는 설명 검색"
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>태스크</InputLabel>
            <Select value={task} onChange={(e) => setTask(e.target.value)} label="태스크">
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="text-generation">Text Generation</MenuItem>
              <MenuItem value="text2text-generation">Text2Text Generation</MenuItem>
              <MenuItem value="question-answering">Question Answering</MenuItem>
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>라이브러리</InputLabel>
            <Select value={library} onChange={(e) => setLibrary(e.target.value)} label="라이브러리">
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="transformers">Transformers</MenuItem>
              <MenuItem value="onnx">ONNX</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            disabled={isLoading}
          >
            검색
          </Button>
        </Box>
      </Paper>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {models && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>모델 ID</TableCell>
                <TableCell>작성자</TableCell>
                <TableCell>크기</TableCell>
                <TableCell>다운로드</TableCell>
                <TableCell>좋아요</TableCell>
                <TableCell>태그</TableCell>
                <TableCell>작업</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {models.map((model: any, idx: number) => (
                <TableRow key={idx}>
                  <TableCell>{model.model_id}</TableCell>
                  <TableCell>{model.author}</TableCell>
                  <TableCell>{model.size}</TableCell>
                  <TableCell>{model.downloads?.toLocaleString() || 0}</TableCell>
                  <TableCell>{model.likes || 0}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {model.is_quantized && (
                        <Chip label="양자화" color="primary" size="small" />
                      )}
                      {model.tags?.slice(0, 2).map((tag: string, tidx: number) => (
                        <Chip key={tidx} label={tag} size="small" />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(model)}
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

      <Dialog open={downloadDialogOpen} onClose={() => setDownloadDialogOpen(false)}>
        <DialogTitle>모델 다운로드</DialogTitle>
        <DialogContent>
          <Typography>
            모델 <strong>{selectedModel?.model_id}</strong>을(를) 다운로드하시겠습니까?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            크기: {selectedModel?.size}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDownloadDialogOpen(false)}>취소</Button>
          <Button
            onClick={() => downloadMutation.mutate(selectedModel.model_id)}
            variant="contained"
            disabled={downloadMutation.isPending}
          >
            {downloadMutation.isPending ? '다운로드 중...' : '다운로드'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HuggingFaceModelsPage;


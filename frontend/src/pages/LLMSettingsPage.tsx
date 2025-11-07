import React, { useState } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Chip,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const LLMSettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProvider, setEditingProvider] = useState<any>(null);
  const [formData, setFormData] = useState({
    provider_name: '',
    api_key: '',
    base_url: '',
    model_name: '',
    is_main_system: true,
  });

  const queryClient = useQueryClient();

  const { data: providers, isLoading } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: async () => {
      const response = await api.get('/llm/providers');
      return response.data.providers;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      await api.post('/llm/providers', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] });
      setDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      await api.put(`/llm/providers/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] });
      setDialogOpen(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/llm/providers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/llm/providers/${id}/toggle`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] });
    },
  });

  const resetForm = () => {
    setFormData({
      provider_name: '',
      api_key: '',
      base_url: '',
      model_name: '',
      is_main_system: true,
    });
    setEditingProvider(null);
  };

  const handleOpenDialog = (provider?: any) => {
    if (provider) {
      setEditingProvider(provider);
      setFormData({
        provider_name: provider.provider_name,
        api_key: '', // 보안상 API 키는 표시하지 않음
        base_url: provider.base_url || '',
        model_name: provider.model_name || '',
        is_main_system: provider.is_main_system,
      });
    } else {
      resetForm();
    }
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editingProvider) {
      updateMutation.mutate({
        id: editingProvider.id,
        data: formData,
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        LLM 설정 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">LLM 설정</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          프로바이더 추가
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>프로바이더</TableCell>
              <TableCell>모델</TableCell>
              <TableCell>시스템 타입</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {providers?.map((provider: any) => (
              <TableRow key={provider.id}>
                <TableCell>{provider.provider_name}</TableCell>
                <TableCell>{provider.model_name || '-'}</TableCell>
                <TableCell>
                  <Chip
                    label={provider.is_main_system ? '메인 시스템' : '선박 시스템'}
                    color={provider.is_main_system ? 'primary' : 'secondary'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={provider.is_active ? '활성' : '비활성'}
                    color={provider.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => handleOpenDialog(provider)}
                    sx={{ mr: 1 }}
                  >
                    수정
                  </Button>
                  <Button
                    size="small"
                    onClick={() => toggleMutation.mutate(provider.id)}
                    sx={{ mr: 1 }}
                  >
                    {provider.is_active ? '비활성화' : '활성화'}
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => {
                      if (window.confirm('정말 삭제하시겠습니까?')) {
                        deleteMutation.mutate(provider.id);
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

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingProvider ? '프로바이더 수정' : '프로바이더 추가'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>프로바이더</InputLabel>
              <Select
                value={formData.provider_name}
                onChange={(e) =>
                  setFormData({ ...formData, provider_name: e.target.value })
                }
                disabled={!!editingProvider}
              >
                <MenuItem value="openai">OpenAI</MenuItem>
                <MenuItem value="claude">Claude (Anthropic)</MenuItem>
                <MenuItem value="gemini">Gemini (Google)</MenuItem>
                <MenuItem value="perplexity">Perplexity</MenuItem>
                <MenuItem value="ollama">Ollama (로컬)</MenuItem>
              </Select>
            </FormControl>

            {formData.provider_name !== 'ollama' && (
              <TextField
                label="API 키"
                type="password"
                value={formData.api_key}
                onChange={(e) =>
                  setFormData({ ...formData, api_key: e.target.value })
                }
                placeholder={editingProvider ? '변경하려면 새 API 키 입력' : 'API 키를 입력하세요'}
                fullWidth
              />
            )}

            {formData.provider_name === 'ollama' && (
              <TextField
                label="Base URL"
                value={formData.base_url}
                onChange={(e) =>
                  setFormData({ ...formData, base_url: e.target.value })
                }
                placeholder="http://localhost:11434"
                fullWidth
              />
            )}

            <TextField
              label="모델명"
              value={formData.model_name}
              onChange={(e) =>
                setFormData({ ...formData, model_name: e.target.value })
              }
              placeholder="예: gpt-3.5-turbo, llama2:7b"
              fullWidth
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_main_system}
                  onChange={(e) =>
                    setFormData({ ...formData, is_main_system: e.target.checked })
                  }
                />
              }
              label="메인 시스템용"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.provider_name}
          >
            {editingProvider ? '수정' : '추가'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LLMSettingsPage;


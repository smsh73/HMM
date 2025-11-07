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
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Sync as SyncIcon, Upload as UploadIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const RAGSyncPage: React.FC = () => {
  const { user } = useAuth();
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [targetSystem, setTargetSystem] = useState('');
  const [importPath, setImportPath] = useState('');
  const queryClient = useQueryClient();

  const { data: syncHistory } = useQuery({
    queryKey: ['rag-sync-history'],
    queryFn: async () => {
      const response = await api.get('/rag-sync/history');
      return response.data.history;
    },
  });

  const exportMutation = useMutation({
    mutationFn: async (target: string) => {
      const response = await api.post('/rag-sync/export', {
        target_system: target,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag-sync-history'] });
      setExportDialogOpen(false);
      setTargetSystem('');
    },
  });

  const importMutation = useMutation({
    mutationFn: async (data: { sync_id?: string; source_path?: string }) => {
      const response = await api.post('/rag-sync/import', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag-sync-history'] });
      setImportDialogOpen(false);
      setImportPath('');
    },
  });

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        RAG 동기화 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">RAG 동기화</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<SyncIcon />}
            onClick={() => setExportDialogOpen(true)}
          >
            내보내기 (메인 → 선박)
          </Button>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => setImportDialogOpen(true)}
          >
            가져오기 (선박 ← 메인)
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          동기화 기록
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>타입</TableCell>
                <TableCell>소스 시스템</TableCell>
                <TableCell>타겟 시스템</TableCell>
                <TableCell>상태</TableCell>
                <TableCell>진행률</TableCell>
                <TableCell>생성일시</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {syncHistory?.map((sync: any) => (
                <TableRow key={sync.id}>
                  <TableCell>
                    <Chip
                      label={sync.sync_type === 'export' ? '내보내기' : '가져오기'}
                      color={sync.sync_type === 'export' ? 'primary' : 'secondary'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{sync.source_system || '-'}</TableCell>
                  <TableCell>{sync.target_system || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={sync.status}
                      color={
                        sync.status === 'completed'
                          ? 'success'
                          : sync.status === 'failed'
                          ? 'error'
                          : 'warning'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{sync.progress}%</TableCell>
                  <TableCell>
                    {sync.created_at
                      ? new Date(sync.created_at).toLocaleString('ko-KR')
                      : '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Dialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>RAG 데이터 내보내기</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="타겟 시스템 식별자"
            value={targetSystem}
            onChange={(e) => setTargetSystem(e.target.value)}
            placeholder="예: ship-001"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>취소</Button>
          <Button
            onClick={() => exportMutation.mutate(targetSystem)}
            variant="contained"
            disabled={!targetSystem || exportMutation.isPending}
          >
            {exportMutation.isPending ? '내보내는 중...' : '내보내기'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>RAG 데이터 가져오기</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="가져올 경로"
            value={importPath}
            onChange={(e) => setImportPath(e.target.value)}
            placeholder="예: /path/to/exported/rag"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>취소</Button>
          <Button
            onClick={() =>
              importMutation.mutate({ source_path: importPath })
            }
            variant="contained"
            disabled={!importPath || importMutation.isPending}
          >
            {importMutation.isPending ? '가져오는 중...' : '가져오기'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RAGSyncPage;


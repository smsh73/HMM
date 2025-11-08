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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Chip,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface Permission {
  id: string;
  document_id: string;
  user_id?: string;
  role?: string;
  permission_type: string;
  created_at: string;
}

const PermissionsPage: React.FC = () => {
  const { user } = useAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<string>('');
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState({
    document_id: '',
    user_id: '',
    role: '',
    permission_type: 'read',
  });
  const queryClient = useQueryClient();

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await api.get('/documents');
      return response.data;
    },
  });

  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      // 사용자 목록 API가 없으므로 현재는 빈 배열
      return [];
    },
    enabled: false,
  });

  const { data: permissions, refetch: refetchPermissions } = useQuery({
    queryKey: ['permissions', selectedDocument],
    queryFn: async () => {
      if (!selectedDocument) return [];
      const response = await api.get(`/permissions/documents/${selectedDocument}`);
      return response.data;
    },
    enabled: !!selectedDocument,
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      await api.post('/permissions', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] });
      setDialogOpen(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/permissions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] });
    },
  });

  const resetForm = () => {
    setFormData({
      document_id: '',
      user_id: '',
      role: '',
      permission_type: 'read',
    });
  };

  const handleOpenDialog = (documentId?: string) => {
    if (documentId) {
      setFormData({
        ...formData,
        document_id: documentId,
      });
    }
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (!formData.document_id) {
      alert('문서를 선택하세요.');
      return;
    }
    if (!formData.user_id && !formData.role) {
      alert('사용자 또는 역할을 선택하세요.');
      return;
    }
    createMutation.mutate(formData);
  };

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        권한 관리 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        권한 관리
      </Typography>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="문서별 권한" />
        <Tab label="전체 권한" />
      </Tabs>

      {tabValue === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <FormControl sx={{ minWidth: 300 }}>
              <InputLabel>문서 선택</InputLabel>
              <Select
                value={selectedDocument}
                onChange={(e) => setSelectedDocument(e.target.value)}
                label="문서 선택"
              >
                {documents?.map((doc: any) => (
                  <MenuItem key={doc.id} value={doc.id}>
                    {doc.filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog(selectedDocument)}
              disabled={!selectedDocument}
            >
              권한 추가
            </Button>
          </Box>

          {selectedDocument && permissions && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>사용자/역할</TableCell>
                    <TableCell>권한 타입</TableCell>
                    <TableCell>설정일</TableCell>
                    <TableCell>작업</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {permissions.map((permission: Permission) => (
                    <TableRow key={permission.id}>
                      <TableCell>
                        {permission.user_id ? (
                          <Chip label={`사용자: ${permission.user_id}`} size="small" />
                        ) : (
                          <Chip
                            label={`역할: ${permission.role}`}
                            color="primary"
                            size="small"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={permission.permission_type}
                          color={
                            permission.permission_type === 'read'
                              ? 'default'
                              : permission.permission_type === 'write'
                              ? 'primary'
                              : 'error'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(permission.created_at).toLocaleString('ko-KR')}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => {
                            if (window.confirm('정말 삭제하시겠습니까?')) {
                              deleteMutation.mutate(permission.id);
                            }
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            전체 문서 목록
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>문서명</TableCell>
                  <TableCell>타입</TableCell>
                  <TableCell>업로드일</TableCell>
                  <TableCell>작업</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents?.map((doc: any) => (
                  <TableRow key={doc.id}>
                    <TableCell>{doc.filename}</TableCell>
                    <TableCell>{doc.file_type}</TableCell>
                    <TableCell>
                      {new Date(doc.upload_date).toLocaleString('ko-KR')}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedDocument(doc.id);
                          setTabValue(0);
                        }}
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(doc.id)}
                      >
                        <AddIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>권한 설정</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>문서</InputLabel>
              <Select
                value={formData.document_id}
                onChange={(e) =>
                  setFormData({ ...formData, document_id: e.target.value })
                }
                label="문서"
              >
                {documents?.map((doc: any) => (
                  <MenuItem key={doc.id} value={doc.id}>
                    {doc.filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>권한 타입</InputLabel>
              <Select
                value={formData.permission_type}
                onChange={(e) =>
                  setFormData({ ...formData, permission_type: e.target.value })
                }
                label="권한 타입"
              >
                <MenuItem value="read">읽기</MenuItem>
                <MenuItem value="write">쓰기</MenuItem>
                <MenuItem value="delete">삭제</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="사용자 ID (선택사항)"
              value={formData.user_id}
              onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
              fullWidth
            />

            <FormControl fullWidth>
              <InputLabel>역할 (선택사항)</InputLabel>
              <Select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                label="역할 (선택사항)"
              >
                <MenuItem value="">없음</MenuItem>
                <MenuItem value="user">사용자</MenuItem>
                <MenuItem value="viewer">뷰어</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.document_id || createMutation.isPending}
          >
            {createMutation.isPending ? '저장 중...' : '저장'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PermissionsPage;

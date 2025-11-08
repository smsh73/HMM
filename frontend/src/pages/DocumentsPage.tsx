import React, { useState } from 'react';
import {
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const DocumentsPage: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await api.get('/documents');
      return response.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/documents/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  if (isLoading) {
    return <CircularProgress />;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">문서 관리</Typography>
        <Button
          variant="contained"
          component="label"
          startIcon={<UploadIcon />}
          disabled={uploading}
        >
          {uploading ? '업로드 중...' : '문서 업로드'}
          <input
            type="file"
            hidden
            onChange={handleFileUpload}
            accept=".pdf,.docx,.doc,.xlsx,.xls,.txt"
          />
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>파일명</TableCell>
              <TableCell>타입</TableCell>
              <TableCell>크기</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>업로드 일시</TableCell>
              <TableCell>작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents?.map((doc: any) => (
              <TableRow key={doc.id}>
                <TableCell>{doc.filename}</TableCell>
                <TableCell>{doc.file_type}</TableCell>
                <TableCell>{(doc.file_size / 1024).toFixed(2)} KB</TableCell>
                <TableCell>
                  {doc.is_indexed ? '인덱싱 완료' : doc.is_parsed ? '파싱 완료' : '대기'}
                </TableCell>
                <TableCell>
                  {new Date(doc.upload_date).toLocaleString('ko-KR')}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => window.location.href = `/documents/${doc.id}`}
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => deleteMutation.mutate(doc.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default DocumentsPage;


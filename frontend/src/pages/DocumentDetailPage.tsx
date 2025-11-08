import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Paper,
  Box,
  CircularProgress,
  Alert,
  Chip,
  Tabs,
  Tab,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const queryClient = useQueryClient();

  const { data: document, isLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const response = await api.get(`/documents/${id}`);
      return response.data;
    },
  });

  const parseMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/documents/${id}/parse`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const indexMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/documents/${id}/index`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const summarizeMutation = useMutation({
    mutationFn: async (summaryType: string) => {
      const response = await api.post(`/summary/documents/${id}`, {
        summary_type: summaryType,
      });
      return response.data;
    },
  });

  if (isLoading) {
    return <CircularProgress />;
  }

  if (!document) {
    return <Alert severity="error">문서를 찾을 수 없습니다.</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">{document.filename}</Typography>
        <Button onClick={() => navigate('/documents')}>목록으로</Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip
            label={document.is_parsed ? '파싱 완료' : '파싱 필요'}
            color={document.is_parsed ? 'success' : 'warning'}
          />
          <Chip
            label={document.is_indexed ? '인덱싱 완료' : '인덱싱 필요'}
            color={document.is_indexed ? 'success' : 'warning'}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          {!document.is_parsed && (
            <Button
              variant="contained"
              onClick={() => parseMutation.mutate()}
              disabled={parseMutation.isPending}
            >
              {parseMutation.isPending ? '파싱 중...' : '파싱'}
            </Button>
          )}
          {document.is_parsed && !document.is_indexed && (
            <Button
              variant="contained"
              onClick={() => indexMutation.mutate()}
              disabled={indexMutation.isPending}
            >
              {indexMutation.isPending ? '인덱싱 중...' : '인덱싱'}
            </Button>
          )}
        </Box>
      </Paper>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
        <Tab label="정보" />
        <Tab label="요약" />
      </Tabs>

      {tabValue === 0 && (
        <Paper sx={{ p: 3, mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            문서 정보
          </Typography>
          <Typography>타입: {document.file_type}</Typography>
          <Typography>크기: {(document.file_size / 1024).toFixed(2)} KB</Typography>
          <Typography>
            업로드 일시: {new Date(document.upload_date).toLocaleString('ko-KR')}
          </Typography>
        </Paper>
      )}

      {tabValue === 1 && (
        <Paper sx={{ p: 3, mt: 2 }}>
          <Box sx={{ mb: 2 }}>
            <Button
              onClick={() => summarizeMutation.mutate('core')}
              disabled={summarizeMutation.isPending}
              sx={{ mr: 1 }}
            >
              핵심 요약
            </Button>
            <Button
              onClick={() => summarizeMutation.mutate('detailed')}
              disabled={summarizeMutation.isPending}
              sx={{ mr: 1 }}
            >
              상세 요약
            </Button>
            <Button
              onClick={() => summarizeMutation.mutate('keywords')}
              disabled={summarizeMutation.isPending}
            >
              키워드
            </Button>
          </Box>

          {summarizeMutation.isPending && <CircularProgress />}
          {summarizeMutation.data && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {summarizeMutation.data.summary_type === 'core' && '핵심 요약'}
                {summarizeMutation.data.summary_type === 'detailed' && '상세 요약'}
                {summarizeMutation.data.summary_type === 'keywords' && '키워드'}
              </Typography>
              <Typography paragraph>{summarizeMutation.data.content}</Typography>
              {summarizeMutation.data.keywords && (
                <Box>
                  <Typography variant="subtitle2">키워드:</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                    {summarizeMutation.data.keywords.map((kw: string, idx: number) => (
                      <Chip key={idx} label={kw} size="small" />
                    ))}
                  </Box>
                </Box>
              )}
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                품질 점수: {summarizeMutation.data.quality_score} | 
                원문 길이: {summarizeMutation.data.original_length} | 
                요약 길이: {summarizeMutation.data.summary_length}
              </Typography>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default DocumentDetailPage;


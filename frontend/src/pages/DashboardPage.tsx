import React from 'react';
import { Typography, Grid, Paper, Box } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const DashboardPage: React.FC = () => {
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await api.get('/documents?limit=10');
      return response.data;
    },
  });

  const stats = {
    totalDocuments: documents?.length || 0,
    parsedDocuments: documents?.filter((d: any) => d.is_parsed).length || 0,
    indexedDocuments: documents?.filter((d: any) => d.is_indexed).length || 0,
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        대시보드
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" color="text.secondary">
              전체 문서
            </Typography>
            <Typography variant="h3">{stats.totalDocuments}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" color="text.secondary">
              파싱 완료
            </Typography>
            <Typography variant="h3">{stats.parsedDocuments}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" color="text.secondary">
              인덱싱 완료
            </Typography>
            <Typography variant="h3">{stats.indexedDocuments}</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;


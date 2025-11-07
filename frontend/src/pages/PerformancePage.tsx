import React from 'react';
import { Typography, Paper, Box, Alert } from '@mui/material';
import { useAuth } from '../hooks/useAuth';

const PerformancePage: React.FC = () => {
  const { user } = useAuth();

  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        성능 모니터링 페이지는 관리자만 접근할 수 있습니다.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        성능 모니터링
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>성능 모니터링 기능은 추후 구현 예정입니다.</Typography>
      </Paper>
    </Box>
  );
};

export default PerformancePage;


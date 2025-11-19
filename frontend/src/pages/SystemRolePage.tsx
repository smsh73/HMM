import React, { useState } from 'react';
import {
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const SystemRolePage: React.FC = () => {
  const [role, setRole] = useState<'main_server' | 'ship_client'>('main_server');
  const [systemName, setSystemName] = useState('');
  const [connectionIp, setConnectionIp] = useState('');
  const [connectionPort, setConnectionPort] = useState(8000);
  const [connectionToken, setConnectionToken] = useState('');
  const queryClient = useQueryClient();

  const { data: currentRole, isLoading } = useQuery({
    queryKey: ['system-role'],
    queryFn: async () => {
      const response = await api.get('/system-role');
      return response.data;
    },
  });

  React.useEffect(() => {
    if (currentRole && currentRole.role) {
      setRole(currentRole.role);
      setSystemName(currentRole.system_name || '');
      setConnectionIp(currentRole.connection_ip || '');
      setConnectionPort(currentRole.connection_port || 8000);
    }
  }, [currentRole]);

  const saveMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/system-role', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-role'] });
      alert('시스템 역할이 설정되었습니다.');
    },
  });

  const handleSave = () => {
    saveMutation.mutate({
      role,
      system_name: systemName,
      connection_ip: role === 'ship_client' ? connectionIp : undefined,
      connection_port: role === 'ship_client' ? connectionPort : undefined,
      connection_token: connectionToken || undefined,
    });
  };

  if (isLoading) {
    return <CircularProgress />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        시스템 역할 설정
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          시스템 역할을 설정하여 메인서버 또는 선박클라이언트로 동작하도록 구성합니다.
        </Alert>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <FormControl fullWidth>
            <InputLabel>시스템 역할</InputLabel>
            <Select
              value={role}
              label="시스템 역할"
              onChange={(e) => setRole(e.target.value as 'main_server' | 'ship_client')}
            >
              <MenuItem value="main_server">메인서버</MenuItem>
              <MenuItem value="ship_client">선박클라이언트</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="시스템 이름"
            value={systemName}
            onChange={(e) => setSystemName(e.target.value)}
            fullWidth
            placeholder="예: Main Server 1, Ship Client 1"
          />

          {role === 'ship_client' && (
            <>
              <TextField
                label="메인서버 IP 주소"
                value={connectionIp}
                onChange={(e) => setConnectionIp(e.target.value)}
                fullWidth
                placeholder="예: 192.168.1.100"
                required
              />

              <TextField
                label="메인서버 포트"
                type="number"
                value={connectionPort}
                onChange={(e) => setConnectionPort(parseInt(e.target.value) || 8000)}
                fullWidth
              />
            </>
          )}

          <TextField
            label="인증 토큰 (선택사항)"
            value={connectionToken}
            onChange={(e) => setConnectionToken(e.target.value)}
            fullWidth
            type="password"
            placeholder="연결 인증용 토큰"
          />

          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saveMutation.isPending}
            fullWidth
            sx={{ mt: 2 }}
          >
            {saveMutation.isPending ? '저장 중...' : '저장'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SystemRolePage;


import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
} from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import shipBg from '../assets/images/ship-bg.jpg';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        backgroundImage: `linear-gradient(rgba(0, 61, 130, 0.7), rgba(0, 61, 130, 0.85)), url(${shipBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
      }}
    >
      <Container maxWidth="sm">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography
              variant="h3"
              sx={{
                color: '#FFFFFF',
                fontWeight: 700,
                mb: 1,
                textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
              }}
            >
              HMM
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: '#FFFFFF',
                fontWeight: 400,
                letterSpacing: '1px',
                textShadow: '0 1px 4px rgba(0, 0, 0, 0.3)',
              }}
            >
              CONNECT VALUES  |  NAVIGATE GROWTH
            </Typography>
          </Box>

          <Paper
            elevation={10}
            sx={{
              padding: 5,
              width: '100%',
              backgroundColor: 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(10px)',
              borderRadius: 3,
            }}
          >
            <Typography component="h1" variant="h4" align="center" gutterBottom>
              GenAI 문서 검색/요약 시스템
            </Typography>
            <Typography
              variant="body1"
              align="center"
              color="text.secondary"
              sx={{ mb: 4, fontWeight: 500 }}
            >
              선박 환경 최적화 AI 시스템
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                margin="normal"
                required
                fullWidth
                label="사용자명"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="비밀번호"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  },
                }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{
                  mt: 2,
                  mb: 2,
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #003D82 0%, #0056B3 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #002A5A 0%, #003D82 100%)',
                  },
                }}
                disabled={loading}
              >
                {loading ? '로그인 중...' : '로그인'}
              </Button>
            </form>

            <Typography
              variant="caption"
              align="center"
              display="block"
              color="text.secondary"
              sx={{ mt: 3 }}
            >
              기본 계정: admin / admin123
            </Typography>
          </Paper>

          <Typography
            variant="body2"
            sx={{
              mt: 4,
              color: 'rgba(255, 255, 255, 0.9)',
              textAlign: 'center',
              textShadow: '0 1px 3px rgba(0, 0, 0, 0.5)',
            }}
          >
            © 2025 HMM Co., Ltd. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default LoginPage;


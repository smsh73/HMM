import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Alert,
} from '@mui/material';
import { Send as SendIcon, Schedule as ScheduleIcon } from '@mui/icons-material';
import api from '../services/api';

interface IndexingCompleteDialogProps {
  open: boolean;
  onClose: () => void;
  documentId: string;
  documentName: string;
}

const IndexingCompleteDialog: React.FC<IndexingCompleteDialogProps> = ({
  open,
  onClose,
  documentId,
  documentName,
}) => {
  const [sendType, setSendType] = useState<'immediate' | 'scheduled' | null>(null);
  const [scheduledAt, setScheduledAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImmediateSend = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. 델타 패키지 생성
      const createResponse = await api.post('/delta-sync/create', {
        document_ids: [documentId],
        package_type: 'document_add',
      });

      const packageId = createResponse.data.package_id;

      // 2. 즉시 전송
      await api.post('/delta-sync/send', {
        package_id: packageId,
        send_type: 'immediate',
      });

      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || '전송 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleScheduledSend = async () => {
    if (!scheduledAt) {
      setError('스케줄 시간을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. 델타 패키지 생성
      const createResponse = await api.post('/delta-sync/create', {
        document_ids: [documentId],
        package_type: 'document_add',
      });

      const packageId = createResponse.data.package_id;

      // 2. 스케줄 전송
      await api.post('/delta-sync/send', {
        package_id: packageId,
        send_type: 'scheduled',
        scheduled_at: scheduledAt,
      });

      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || '전송 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setSendType(null);
    setScheduledAt('');
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
      <DialogTitle>
        벡터 임베딩 완료
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body1" gutterBottom>
            문서 <strong>'{documentName}'</strong>의 벡터 임베딩이 완료되었습니다.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            벡터DB와 인덱스가 업데이트되었습니다. 선박 클라이언트로 전송하시겠습니까?
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {sendType === null && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => setSendType('immediate')}
              fullWidth
            >
              즉시 전송
            </Button>
            <Button
              variant="outlined"
              startIcon={<ScheduleIcon />}
              onClick={() => setSendType('scheduled')}
              fullWidth
            >
              스케줄 전송
            </Button>
          </Box>
        )}

        {sendType === 'scheduled' && (
          <Box sx={{ mt: 2 }}>
            <TextField
              label="전송 시간"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              fullWidth
              InputLabelProps={{
                shrink: true,
              }}
            />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} disabled={loading}>
          취소
        </Button>
        {sendType === 'immediate' && (
          <Button
            onClick={handleImmediateSend}
            variant="contained"
            disabled={loading}
          >
            전송
          </Button>
        )}
        {sendType === 'scheduled' && (
          <Button
            onClick={handleScheduledSend}
            variant="contained"
            disabled={loading || !scheduledAt}
          >
            스케줄 등록
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default IndexingCompleteDialog;


import React, { useState, useRef, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Drawer,
  IconButton,
  ListItemButton,
} from '@mui/material';
import { Send as SendIcon, SmartToy as AIIcon, Person as PersonIcon, Menu as MenuIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
}

const ChatPage: React.FC = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [useRAG, setUseRAG] = useState(true);
  const [useMainSystem, setUseMainSystem] = useState(true);
  const [provider, setProvider] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationsDrawerOpen, setConversationsDrawerOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: providers } = useQuery({
    queryKey: ['llm-providers', useMainSystem],
    queryFn: async () => {
      const response = await api.get('/llm/providers', {
        params: { is_main_system: useMainSystem },
      });
      return response.data.providers;
    },
  });

  const { data: conversations } = useQuery({
    queryKey: ['chat-conversations'],
    queryFn: async () => {
      const response = await api.get('/chat/conversations');
      return response.data.conversations;
    },
  });

  const { data: chatHistory, refetch: refetchHistory } = useQuery({
    queryKey: ['chat-history', conversationId],
    queryFn: async () => {
      if (!conversationId) return { messages: [] };
      const response = await api.get('/chat/history', {
        params: { conversation_id: conversationId },
      });
      return response.data;
    },
    enabled: !!conversationId,
  });

  useEffect(() => {
    if (chatHistory?.messages) {
      const loadedMessages = chatHistory.messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        sources: msg.sources,
        timestamp: new Date(msg.created_at),
      }));
      setMessages(loadedMessages);
    }
  }, [chatHistory]);

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await api.post('/chat/', {
        message,
        conversation_id: conversationId,
        use_rag: useRAG,
        use_main_system: useMainSystem,
        provider_name: provider || undefined,
      });
      return response.data;
    },
    onSuccess: (data) => {
      const userMessage: Message = {
        role: 'user',
        content: input,
        timestamp: new Date(),
      };
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setInput('');
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        refetchHistory();
      }
      // 대화 목록 새로고침
      queryClient.invalidateQueries({ queryKey: ['chat-conversations'] });
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/chat/conversations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-conversations'] });
      if (conversationId === conversations?.find((c: any) => c.id === conversationId)?.id) {
        setConversationId(null);
        setMessages([]);
      }
    },
  });

  const queryClient = useQueryClient();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;
    chatMutation.mutate(input);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSelectConversation = (id: string) => {
    setConversationId(id);
    setConversationsDrawerOpen(false);
  };

  const handleNewConversation = () => {
    setConversationId(null);
    setMessages([]);
    setConversationsDrawerOpen(false);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)' }}>
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <IconButton onClick={() => setConversationsDrawerOpen(true)}>
          <MenuIcon />
        </IconButton>
        <Typography variant="h4">AI 채팅</Typography>
        <FormControlLabel
          control={
            <Switch checked={useRAG} onChange={(e) => setUseRAG(e.target.checked)} />
          }
          label="RAG 사용"
        />
        <FormControlLabel
          control={
            <Switch
              checked={useMainSystem}
              onChange={(e) => setUseMainSystem(e.target.checked)}
            />
          }
          label="메인 시스템"
        />
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>프로바이더</InputLabel>
          <Select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            label="프로바이더"
          >
            <MenuItem value="">기본</MenuItem>
            {providers
              ?.filter((p: any) => p.is_active)
              .map((p: any) => (
                <MenuItem key={p.id} value={p.provider_name}>
                  {p.provider_name} ({p.provider_name || 'default'})
                </MenuItem>
              ))}
          </Select>
        </FormControl>
      </Box>

      <Drawer
        anchor="left"
        open={conversationsDrawerOpen}
        onClose={() => setConversationsDrawerOpen(false)}
      >
        <Box sx={{ width: 300, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            대화 목록
          </Typography>
          <Button
            variant="contained"
            fullWidth
            sx={{ mb: 2 }}
            onClick={handleNewConversation}
          >
            새 대화
          </Button>
          <List>
            {conversations?.map((conv: any) => (
              <ListItem
                key={conv.id}
                secondaryAction={
                  <IconButton
                    edge="end"
                    onClick={() => deleteConversationMutation.mutate(conv.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                }
                disablePadding
              >
                <ListItemButton
                  selected={conversationId === conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                >
                  <ListItemText
                    primary={conv.title}
                    secondary={new Date(conv.updated_at).toLocaleString('ko-KR')}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      <Paper
        sx={{
          flex: 1,
          p: 2,
          overflow: 'auto',
          mb: 2,
          bgcolor: 'grey.50',
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'text.secondary',
            }}
          >
            <AIIcon sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h6">AI와 대화를 시작하세요</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              질문을 입력하면 AI가 답변해드립니다.
            </Typography>
          </Box>
        ) : (
          <List>
            {messages.map((msg, idx) => (
              <ListItem
                key={idx}
                sx={{
                  flexDirection: 'column',
                  alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 0.5,
                    width: '100%',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  {msg.role === 'user' ? <PersonIcon /> : <AIIcon />}
                  <Typography variant="caption" color="text.secondary">
                    {msg.role === 'user' ? '사용자' : 'AI'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {msg.timestamp.toLocaleTimeString('ko-KR')}
                  </Typography>
                </Box>
                <Paper
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    bgcolor: msg.role === 'user' ? 'primary.light' : 'background.paper',
                    color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  }}
                >
                  <Typography
                    variant="body1"
                    sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                  >
                    {msg.content}
                  </Typography>
                  {msg.sources && msg.sources.length > 0 && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                        참고 문서:
                      </Typography>
                      {msg.sources.map((source, sidx) => (
                        <Chip
                          key={sidx}
                          label={`문서 ${sidx + 1} (${(source.score * 100).toFixed(1)}%)`}
                          size="small"
                          sx={{ mr: 0.5, mt: 0.5 }}
                        />
                      ))}
                    </Box>
                  )}
                </Paper>
              </ListItem>
            ))}
            {chatMutation.isPending && (
              <ListItem>
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ ml: 2 }}>
                  AI가 답변을 생성하는 중...
                </Typography>
              </ListItem>
            )}
            <div ref={messagesEndRef} />
          </List>
        )}
      </Paper>

      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="메시지를 입력하세요..."
          disabled={chatMutation.isPending}
        />
        <Button
          variant="contained"
          startIcon={<SendIcon />}
          onClick={handleSend}
          disabled={!input.trim() || chatMutation.isPending}
          sx={{ minWidth: 120 }}
        >
          {chatMutation.isPending ? '전송 중...' : '전송'}
        </Button>
      </Box>

      {chatMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          메시지 전송 중 오류가 발생했습니다.
        </Alert>
      )}
    </Box>
  );
};

export default ChatPage;

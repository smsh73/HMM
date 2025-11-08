import React, { useState } from 'react';
import {
  Typography,
  TextField,
  Button,
  Paper,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Checkbox,
  FormControlLabel,
  CircularProgress,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [generateAnswer, setGenerateAnswer] = useState(false);

  const searchMutation = useMutation({
    mutationFn: async (searchQuery: string) => {
      const response = await api.post('/search', {
        query: searchQuery,
        top_k: 5,
        generate_answer: generateAnswer,
      });
      return response.data;
    },
  });

  const handleSearch = () => {
    if (query.trim()) {
      searchMutation.mutate(query);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        문서 검색
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            label="검색어"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            disabled={searchMutation.isPending}
          >
            검색
          </Button>
        </Box>
        <FormControlLabel
          control={
            <Checkbox
              checked={generateAnswer}
              onChange={(e) => setGenerateAnswer(e.target.checked)}
            />
          }
          label="LLM 기반 답변 생성"
        />
      </Paper>

      {searchMutation.isPending && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {searchMutation.data && (
        <Box>
          {searchMutation.data.answer && (
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
              <Typography variant="h6" gutterBottom>
                답변
              </Typography>
              <Typography>{searchMutation.data.answer.answer}</Typography>
              <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                신뢰도: {(searchMutation.data.answer.confidence * 100).toFixed(1)}%
              </Typography>
            </Paper>
          )}

          <Typography variant="h6" gutterBottom>
            검색 결과 ({searchMutation.data.total_results}개)
          </Typography>

          <List>
            {searchMutation.data.results.map((result: any, idx: number) => (
              <Paper key={idx} sx={{ mb: 2, p: 2 }}>
                <ListItem>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`유사도: ${(result.score * 100).toFixed(1)}%`}
                          size="small"
                          color="primary"
                        />
                        <Typography variant="body2" color="text.secondary">
                          문서 ID: {result.document_id}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Typography
                        variant="body2"
                        sx={{
                          mt: 1,
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}
                      >
                        {result.content}
                      </Typography>
                    }
                  />
                </ListItem>
              </Paper>
            ))}
          </List>
        </Box>
      )}
    </Box>
  );
};

export default SearchPage;


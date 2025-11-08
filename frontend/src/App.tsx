import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import SearchPage from './pages/SearchPage';
import DocumentDetailPage from './pages/DocumentDetailPage';
import PermissionsPage from './pages/PermissionsPage';
import PerformancePage from './pages/PerformancePage';
import LLMSettingsPage from './pages/LLMSettingsPage';
import ModelManagementPage from './pages/ModelManagementPage';
import RAGSyncPage from './pages/RAGSyncPage';
import ChatPage from './pages/ChatPage';
import { AuthProvider, useAuth } from './hooks/useAuth';

function AppContent() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          isAuthenticated ? (
            <Layout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/documents" element={<DocumentsPage />} />
                <Route path="/documents/:id" element={<DocumentDetailPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/permissions" element={<PermissionsPage />} />
                <Route path="/performance" element={<PerformancePage />} />
                <Route path="/llm-settings" element={<LLMSettingsPage />} />
                <Route path="/models" element={<ModelManagementPage />} />
                <Route path="/rag-sync" element={<RAGSyncPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;


import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './stores/AuthContext';
import { RequireAuth } from './components/PermissionGuard';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { ProjectDetail } from './pages/ProjectDetail';
import { MarketPage } from './pages/MarketPage';
import { EngineeringPage } from './pages/EngineeringPage';
import { FinancePage } from './pages/FinancePage';
import { Statistics } from './pages/Statistics';
import { AttachmentsPage } from './pages/AttachmentsPage';
import { Settings } from './pages/Settings';
import { UserManagement } from './pages/UserManagement';
import { MyAccount } from './pages/MyAccount';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/"
                element={
                  <RequireAuth>
                    <Layout />
                  </RequireAuth>
                }
              >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="projects" element={<Projects />} />
                <Route path="projects/:id" element={<ProjectDetail />} />
                {/* 新增的项目附件子路由 */}
                <Route path="projects/:id/attachments" element={<AttachmentsPage />} />
                <Route path="market" element={<MarketPage />} />
                <Route path="engineering" element={<EngineeringPage />} />
                <Route path="finance" element={<FinancePage />} />
                <Route path="statistics" element={<Statistics />} />
                <Route path="attachments" element={<AttachmentsPage />} />
                <Route path="settings" element={<Settings />} />
                <Route path="users" element={<UserManagement />} />
                <Route path="my-account" element={<MyAccount />} />
              </Route>
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ConfigProvider>
    </QueryClientProvider>
  );
};

export default App;

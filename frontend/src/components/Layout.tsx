import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout as AntLayout, Menu, Button, Dropdown, Avatar, Space, theme } from 'antd';
import {
  DashboardOutlined,
  ProjectOutlined,
  ShopOutlined,
  ToolOutlined,
  DollarOutlined,
  BarChartOutlined,
  FileOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuth } from '../stores/AuthContext';
import { getDepartmentText } from '../utils';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/projects', icon: <ProjectOutlined />, label: 'Projects' },
  { key: '/market', icon: <ShopOutlined />, label: 'Market Data' },
  { key: '/engineering', icon: <ToolOutlined />, label: 'Engineering Data' },
  { key: '/finance', icon: <DollarOutlined />, label: 'Finance Data' },
  { key: '/statistics', icon: <BarChartOutlined />, label: 'Statistics' },
  { key: '/attachments', icon: <FileOutlined />, label: 'Attachments' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
];

export const Layout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { token } = theme.useToken();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const userMenuItems = [
    {
      key: 'profile',
      label: (
        <Space>
          <UserOutlined />
          {user?.username} ({getDepartmentText(user?.department || 'admin')})
        </Space>
      ),
      disabled: true,
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      label: (
        <Space>
          <LogoutOutlined />
          Logout
        </Space>
      ),
      onClick: () => {
        logout();
        navigate('/login');
      },
    },
  ];

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{ background: token.colorBgContainer }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <h2 style={{ margin: 0, color: token.colorPrimary }}>
            {collapsed ? 'MIS' : 'Cross-Dept MIS'}
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none' }}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            padding: '0 24px',
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              {!collapsed && user?.username}
            </Space>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: token.colorBgContainer,
            borderRadius: token.borderRadiusLG,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

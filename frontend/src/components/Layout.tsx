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
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useAuth } from '../stores/AuthContext';
import { getDepartmentText } from '../utils';

const { Header, Sider, Content } = AntLayout;

const getMenuItems = (isAdmin: boolean) => {
  const baseItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
    { key: '/projects', icon: <ProjectOutlined />, label: '项目管理' },
    { key: '/market', icon: <ShopOutlined />, label: '市场数据' },
    { key: '/engineering', icon: <ToolOutlined />, label: '工程数据' },
    { key: '/finance', icon: <DollarOutlined />, label: '财务数据' },
    { key: '/statistics', icon: <BarChartOutlined />, label: '统计报表' },
    { key: '/attachments', icon: <FileOutlined />, label: '附件中心' },
  ];

  if (isAdmin) {
    baseItems.push({ key: '/users', icon: <TeamOutlined />, label: '用户管理' });
  } else {
    baseItems.push({ key: '/my-account', icon: <UserOutlined />, label: '我的账户' });
  }

  return baseItems;
};

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
          退出登录
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
            {collapsed ? 'MIS' : '跨部门管理系统'}
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={getMenuItems(user?.department === 'admin')}
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

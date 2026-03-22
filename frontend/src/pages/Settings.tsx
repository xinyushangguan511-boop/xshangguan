import React from 'react';
import { Card, Descriptions, Typography, Tag } from 'antd';
import { useAuth } from '../stores/AuthContext';
import { getDepartmentColor, getDepartmentText } from '../utils';
import dayjs from 'dayjs';

const { Title } = Typography;

export const Settings: React.FC = () => {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div>
      <Title level={4}>系统设置</Title>

      <Card title="个人信息">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
          <Descriptions.Item label="所属部门">
            <Tag color={getDepartmentColor(user.department)}>
              {getDepartmentText(user.department)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="账户状态">
            <Tag color={user.is_active ? 'green' : 'red'}>
              {user.is_active ? '正常' : '已禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(user.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="权限信息" style={{ marginTop: 16 }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="创建项目">
            {user.department === 'market' || user.department === 'admin' ? '是' : '否'}
          </Descriptions.Item>
          <Descriptions.Item label="编辑市场数据">
            {user.department === 'market' || user.department === 'admin' ? '是' : '否'}
          </Descriptions.Item>
          <Descriptions.Item label="编辑工程数据">
            {user.department === 'engineering' || user.department === 'admin' ? '是' : '否'}
          </Descriptions.Item>
          <Descriptions.Item label="编辑财务数据">
            {user.department === 'finance' || user.department === 'admin' ? '是' : '否'}
          </Descriptions.Item>
          <Descriptions.Item label="更新项目状态">
            {user.department === 'engineering' || user.department === 'market' || user.department === 'admin' ? '是' : '否'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

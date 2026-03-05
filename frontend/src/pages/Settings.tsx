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
      <Title level={4}>User Settings</Title>

      <Card title="Profile Information">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Username">{user.username}</Descriptions.Item>
          <Descriptions.Item label="Department">
            <Tag color={getDepartmentColor(user.department)}>
              {getDepartmentText(user.department)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Account Status">
            <Tag color={user.is_active ? 'green' : 'red'}>
              {user.is_active ? 'Active' : 'Inactive'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Created At">
            {dayjs(user.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Permissions" style={{ marginTop: 16 }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Create Projects">
            {user.department === 'market' || user.department === 'admin' ? 'Yes' : 'No'}
          </Descriptions.Item>
          <Descriptions.Item label="Edit Market Data">
            {user.department === 'market' || user.department === 'admin' ? 'Yes' : 'No'}
          </Descriptions.Item>
          <Descriptions.Item label="Edit Engineering Data">
            {user.department === 'engineering' || user.department === 'admin' ? 'Yes' : 'No'}
          </Descriptions.Item>
          <Descriptions.Item label="Edit Finance Data">
            {user.department === 'finance' || user.department === 'admin' ? 'Yes' : 'No'}
          </Descriptions.Item>
          <Descriptions.Item label="Update Project Status">
            {user.department === 'engineering' || user.department === 'market' || user.department === 'admin' ? 'Yes' : 'No'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

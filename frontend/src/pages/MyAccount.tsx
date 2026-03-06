import React, { useEffect } from 'react';
import { Card, Form, Input, Button, message, Descriptions, Tag } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { authApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { getDepartmentText, getDepartmentColor } from '../utils';

export const MyAccount: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (user) {
      profileForm.setFieldsValue({
        real_name: user.real_name,
        phone: user.phone,
        email: user.email,
      });
    }
  }, [user, profileForm]);

  const profileMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: () => {
      message.success('个人信息更新成功');
      refreshUser();
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
    onError: () => message.error('个人信息更新失败'),
  });

  const passwordMutation = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => {
      message.success('密码修改成功');
      passwordForm.resetFields();
    },
    onError: () => message.error('当前密码错误'),
  });

  const handleProfileSubmit = async () => {
    const values = await profileForm.validateFields();
    profileMutation.mutate(values);
  };

  const handlePasswordSubmit = async () => {
    const values = await passwordForm.validateFields();
    passwordMutation.mutate({
      current_password: values.current_password,
      new_password: values.new_password,
    });
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>我的账户</h2>

      <Card title="账户信息" style={{ marginBottom: 24 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
          <Descriptions.Item label="部门">
            <Tag color={getDepartmentColor(user?.department || 'admin')}>
              {getDepartmentText(user?.department || 'admin')}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="账户状态">
            <Tag color={user?.is_active ? 'green' : 'red'}>
              {user?.is_active ? '正常' : '已禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {user?.created_at ? dayjs(user.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="个人信息" style={{ marginBottom: 24 }}>
        <Form
          form={profileForm}
          layout="vertical"
          style={{ maxWidth: 400 }}
        >
          <Form.Item name="real_name" label="姓名">
            <Input placeholder="请输入您的真实姓名" />
          </Form.Item>

          <Form.Item name="phone" label="手机号码">
            <Input placeholder="请输入手机号码" />
          </Form.Item>

          <Form.Item name="email" label="电子邮箱">
            <Input type="email" placeholder="请输入电子邮箱" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              onClick={handleProfileSubmit}
              loading={profileMutation.isPending}
            >
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="修改密码">
        <Form
          form={passwordForm}
          layout="vertical"
          style={{ maxWidth: 400 }}
        >
          <Form.Item
            name="current_password"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password placeholder="请输入当前密码" />
          </Form.Item>

          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="确认新密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              onClick={handlePasswordSubmit}
              loading={passwordMutation.isPending}
            >
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

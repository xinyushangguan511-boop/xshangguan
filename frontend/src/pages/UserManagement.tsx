import React, { useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Space, message, Popconfirm, Tag, Switch } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, KeyOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { usersApi } from '../services/api';
import { getDepartmentText, getDepartmentColor } from '../utils';
import type { User, Department } from '../types';

export const UserManagement: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
  });

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      message.success('用户创建成功');
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('用户创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<User> }) => usersApi.update(id, data),
    onSuccess: () => {
      message.success('用户更新成功');
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setModalOpen(false);
      setEditingUser(null);
      form.resetFields();
    },
    onError: () => message.error('用户更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      message.success('用户删除成功');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: () => message.error('用户删除失败'),
  });

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, password }: { id: string; password: string }) =>
      usersApi.resetPassword(id, password),
    onSuccess: () => {
      message.success('密码重置成功');
      setPasswordModalOpen(false);
      setSelectedUserId(null);
      passwordForm.resetFields();
    },
    onError: () => message.error('密码重置失败'),
  });

  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      form.setFieldsValue({
        username: user.username,
        department: user.department,
        real_name: user.real_name,
        phone: user.phone,
        email: user.email,
        is_active: user.is_active,
      });
    } else {
      setEditingUser(null);
      form.resetFields();
      form.setFieldsValue({ is_active: true });
    }
    setModalOpen(true);
  };

  const handleOpenPasswordModal = (userId: string) => {
    setSelectedUserId(userId);
    passwordForm.resetFields();
    setPasswordModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingUser) {
      const { password, ...updateData } = values;
      updateMutation.mutate({ id: editingUser.id, data: updateData });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleResetPassword = async () => {
    const values = await passwordForm.validateFields();
    if (selectedUserId) {
      resetPasswordMutation.mutate({ id: selectedUserId, password: values.new_password });
    }
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', width: 120 },
    { title: '姓名', dataIndex: 'real_name', width: 100, render: (v: string) => v || '-' },
    {
      title: '部门',
      dataIndex: 'department',
      width: 100,
      render: (dept: Department) => (
        <Tag color={getDepartmentColor(dept)}>{getDepartmentText(dept)}</Tag>
      ),
    },
    { title: '手机', dataIndex: 'phone', width: 130, render: (v: string) => v || '-' },
    { title: '邮箱', dataIndex: 'email', width: 180, render: (v: string) => v || '-' },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: User) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleOpenModal(record)} />
          <Button
            type="link"
            icon={<KeyOutlined />}
            onClick={() => handleOpenPasswordModal(record.id)}
            title="重置密码"
          />
          <Popconfirm
            title="确定删除该用户？"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>用户管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
          新增用户
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1000 }}
      />

      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingUser(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={500}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
            ]}
          >
            <Input disabled={!!editingUser} />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="初始密码"
              rules={[
                { required: true, message: '请输入初始密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password />
            </Form.Item>
          )}

          <Form.Item
            name="department"
            label="部门"
            rules={[{ required: true, message: '请选择部门' }]}
          >
            <Select>
              <Select.Option value="admin">管理员</Select.Option>
              <Select.Option value="market">市场部</Select.Option>
              <Select.Option value="engineering">工程部</Select.Option>
              <Select.Option value="finance">财务部</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="real_name" label="姓名">
            <Input />
          </Form.Item>

          <Form.Item name="phone" label="手机">
            <Input />
          </Form.Item>

          <Form.Item name="email" label="邮箱">
            <Input type="email" />
          </Form.Item>

          {editingUser && (
            <Form.Item name="is_active" label="状态" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>

      <Modal
        title="重置密码"
        open={passwordModalOpen}
        onOk={handleResetPassword}
        onCancel={() => {
          setPasswordModalOpen(false);
          setSelectedUserId(null);
          passwordForm.resetFields();
        }}
        confirmLoading={resetPasswordMutation.isPending}
        width={400}
        okText="确定"
        cancelText="取消"
      >
        <Form form={passwordForm} layout="vertical">
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="确认密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认密码' },
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
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

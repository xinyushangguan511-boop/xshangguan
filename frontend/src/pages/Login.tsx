import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message, Typography, Select } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../stores/AuthContext';
import { authApi } from '../services/api';
import type { Department } from '../types';

const { Title } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm extends LoginForm {
  department: Department;
}

export const Login: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleLogin = async (values: LoginForm) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('Login successful');
      navigate('/dashboard');
    } catch {
      message.error('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterForm) => {
    setLoading(true);
    try {
      await authApi.register(values.username, values.password, values.department);
      message.success('Registration successful. Please login.');
      setIsRegister(false);
      form.resetFields();
    } catch {
      message.error('Registration failed. Username may already exist.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 32 }}>
          {isRegister ? 'Register' : 'Login'}
        </Title>
        <Form
          form={form}
          name={isRegister ? 'register' : 'login'}
          onFinish={isRegister ? handleRegister : handleLogin}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: 'Please input your username!' },
              { min: 3, message: 'Username must be at least 3 characters' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="Username" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Please input your password!' },
              { min: 6, message: 'Password must be at least 6 characters' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Password" />
          </Form.Item>

          {isRegister && (
            <Form.Item
              name="department"
              rules={[{ required: true, message: 'Please select your department!' }]}
            >
              <Select placeholder="Select Department">
                <Select.Option value="market">Marketing</Select.Option>
                <Select.Option value="engineering">Engineering</Select.Option>
                <Select.Option value="finance">Finance</Select.Option>
                <Select.Option value="admin">Admin</Select.Option>
              </Select>
            </Form.Item>
          )}

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {isRegister ? 'Register' : 'Login'}
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Button type="link" onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

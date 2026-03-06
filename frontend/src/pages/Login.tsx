import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message, Typography, Alert, Spin } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../stores/AuthContext';
import { authApi } from '../services/api';

const { Title, Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm extends LoginForm {
  // First user is always admin, no department selection needed
}

export const Login: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [registrationAllowed, setRegistrationAllowed] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  useEffect(() => {
    const checkRegistrationStatus = async () => {
      try {
        const status = await authApi.registrationStatus();
        setRegistrationAllowed(status.registration_allowed);
        // If registration is allowed (no admin yet), show register form
        if (status.registration_allowed) {
          setIsRegister(true);
        }
      } catch {
        // If API fails, assume registration is not allowed
        setRegistrationAllowed(false);
      } finally {
        setCheckingStatus(false);
      }
    };
    checkRegistrationStatus();
  }, []);

  const handleLogin = async (values: LoginForm) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('登录成功');
      navigate('/dashboard');
    } catch {
      message.error('用户名或密码错误');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterForm) => {
    setLoading(true);
    try {
      // First user is always admin
      await authApi.register(values.username, values.password, 'admin');
      message.success('管理员账户创建成功，请登录');
      setIsRegister(false);
      setRegistrationAllowed(false);
      form.resetFields();
    } catch {
      message.error('注册失败，用户名可能已存在');
    } finally {
      setLoading(false);
    }
  };

  if (checkingStatus) {
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
        <Spin size="large" />
      </div>
    );
  }

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
        <Title level={2} style={{ textAlign: 'center', marginBottom: 16 }}>
          {isRegister ? '创建管理员账户' : '用户登录'}
        </Title>

        {isRegister && registrationAllowed && (
          <Alert
            message="首次使用"
            description="请创建管理员账户。创建后，其他用户需由管理员在系统内添加。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          form={form}
          name={isRegister ? 'register' : 'login'}
          onFinish={isRegister ? handleRegister : handleLogin}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {isRegister ? '创建管理员账户' : '登录'}
            </Button>
          </Form.Item>

          {/* Only show toggle if registration is allowed */}
          {registrationAllowed && (
            <div style={{ textAlign: 'center' }}>
              <Button type="link" onClick={() => setIsRegister(!isRegister)}>
                {isRegister ? '已有账号？去登录' : '创建管理员账户'}
              </Button>
            </div>
          )}

          {/* Show message if registration is closed */}
          {!registrationAllowed && !isRegister && (
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">
                如需创建账户，请联系管理员
              </Text>
            </div>
          )}
        </Form>
      </Card>
    </div>
  );
};

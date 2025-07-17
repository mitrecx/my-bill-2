import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';
import type { LoginRequest } from '../types';
import japanroad from '../assets/japanroad.jpeg';
import japanroad2 from '../assets/japanroad2.jpeg';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [form] = Form.useForm();
  const [backgroundImage, setBackgroundImage] = useState<string>('');

  // 添加自定义样式
  const customStyles = `
    .glass-form .ant-input::placeholder,
        .glass-form .ant-input-password input::placeholder {
          color: rgba(255, 255, 255, 0.6) !important;
          font-size: 18px !important;
        }
        
        .glass-form .ant-input,
        .glass-form .ant-input-password input {
          font-size: 18px !important;
          color: #ffffff !important;
        }
    
    .glass-form .ant-input:focus,
    .glass-form .ant-input-password:focus,
    .glass-form .ant-input-focused {
      border-color: rgba(255, 255, 255, 0.5) !important;
      box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 彻底修复浏览器自动填充时的背景色问题 - 保持透明毛玻璃效果 */
    .glass-form .ant-input:-webkit-autofill,
    .glass-form .ant-input:-webkit-autofill:hover,
    .glass-form .ant-input:-webkit-autofill:focus,
    .glass-form .ant-input:-webkit-autofill:active,
    .glass-form .ant-input-password input:-webkit-autofill,
    .glass-form .ant-input-password input:-webkit-autofill:hover,
    .glass-form .ant-input-password input:-webkit-autofill:focus,
    .glass-form .ant-input-password input:-webkit-autofill:active {
      -webkit-box-shadow: 0 0 0 1000px transparent inset !important;
      -webkit-text-fill-color: #ffffff !important;
      background-color: transparent !important;
      background-image: none !important;
      transition: background-color 5000s ease-in-out 0s !important;
    }
    
    /* Firefox 自动填充样式 */
    .glass-form .ant-input:-moz-autofill,
    .glass-form .ant-input-password input:-moz-autofill {
      background-color: transparent !important;
      background-image: none !important;
      color: #ffffff !important;
      box-shadow: none !important;
    }
    
    /* 强制覆盖所有可能的自动填充样式 */
    .glass-form .ant-input[autocomplete],
    .glass-form .ant-input-password input[autocomplete] {
      background-color: transparent !important;
      background-image: none !important;
    }

    /* 鲜艳彩虹按钮样式 */
    .rainbow-login-button {
      background: linear-gradient(135deg, 
        rgba(255, 105, 180, 0.7) 0%,   /* 鲜艳的粉色 */
        rgba(255, 140, 105, 0.7) 20%,  /* 鲜艳的橙色 */
        rgba(255, 215, 0, 0.7) 40%,    /* 鲜艳的金黄色 */
        rgba(50, 205, 50, 0.7) 60%,    /* 鲜艳的绿色 */
        rgba(30, 144, 255, 0.7) 80%,   /* 鲜艳的蓝色 */
        rgba(138, 43, 226, 0.7) 100%   /* 鲜艳的紫色 */
      ) !important;
      background-size: 200% 200% !important;
      animation: rainbow-shift 6s ease-in-out infinite !important;
      border: 1px solid rgba(255, 255, 255, 0.8) !important;
      backdrop-filter: blur(10px) !important;
      transition: all 0.3s ease !important;
      box-shadow: 0 2px 12px rgba(255, 255, 255, 0.4) !important;
    }

    .rainbow-login-button:hover {
      background: linear-gradient(135deg, 
        rgba(255, 105, 180, 0.75) 0%,  /* 轻微增强的粉色 */
        rgba(255, 140, 105, 0.75) 20%, /* 轻微增强的橙色 */
        rgba(255, 215, 0, 0.75) 40%,   /* 轻微增强的金黄色 */
        rgba(50, 205, 50, 0.75) 60%,   /* 轻微增强的绿色 */
        rgba(30, 144, 255, 0.75) 80%,  /* 轻微增强的蓝色 */
        rgba(138, 43, 226, 0.75) 100%  /* 轻微增强的紫色 */
      ) !important;
      transform: translateY(-0.5px) !important;
      box-shadow: 0 3px 15px rgba(255, 255, 255, 0.45) !important;
      border-color: rgba(255, 255, 255, 0.85) !important;
    }

    @keyframes rainbow-shift {
      0%, 100% {
        background-position: 0% 50%;
      }
      50% {
        background-position: 100% 50%;
      }
    }
  `;

  // 根据时间选择背景图片
  const getBackgroundImage = () => {
    const now = new Date();
    const hour = now.getHours();
    
    // 早上6:00到晚上18:00使用japanroad，其他时间使用japanroad2
    if (hour >= 6 && hour < 18) {
      return japanroad;
    } else {
      return japanroad2;
    }
  };

  useEffect(() => {
    // 初始设置背景图片
    setBackgroundImage(getBackgroundImage());
    
    // 每分钟检查一次时间，更新背景图片
    const interval = setInterval(() => {
      setBackgroundImage(getBackgroundImage());
    }, 60000); // 60秒检查一次
    
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (values: LoginRequest) => {
    try {
      clearError();
      await login(values);
      navigate('/dashboard');
    } catch (error) {
      // 错误已经在store中处理
    }
  };

  return (
    <>
      <style>{customStyles}</style>
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        padding: '20px',
        transition: 'background-image 0.5s ease-in-out',
      }}>
      <Card style={{ 
        width: '100%',
        maxWidth: '480px',
        minWidth: '320px',
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        WebkitBackdropFilter: 'blur(20px)', // Safari 兼容性
      }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ 
              margin: 0,
              color: '#ffffff',
              textShadow: '0 2px 4px rgba(0, 0, 0, 0.5)',
              fontWeight: 600
            }}>
              家庭账单管理
            </Title>
            <Text type="secondary" style={{ 
              color: 'rgba(255, 255, 255, 0.8)',
              textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)'
            }}>
              请登录您的账户
            </Text>
          </div>

          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={clearError}
            />
          )}

          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            autoComplete="off"
            size="large"
            className="glass-form"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input
                prefix={<UserOutlined style={{ color: 'rgba(255, 255, 255, 0.7)' }} />}
                placeholder="用户名"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  color: '#ffffff',
                  borderRadius: '8px',
                }}
                styles={{
                  input: {
                    backgroundColor: 'transparent',
                    color: '#ffffff',
                  }
                }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: 'rgba(255, 255, 255, 0.7)' }} />}
                placeholder="密码"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  color: '#ffffff',
                  borderRadius: '8px',
                }}
                styles={{
                  input: {
                    backgroundColor: 'transparent',
                    color: '#ffffff',
                  }
                }}
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={isLoading}
                className="rainbow-login-button"
                style={{ 
                  width: '100%',
                  borderRadius: '8px',
                  fontWeight: 600,
                  height: '44px',
                  color: '#ffffff',
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.4)',
                  fontSize: '18px',
                  letterSpacing: '2px',
                }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          {/* <div style={{ textAlign: 'center' }}>
            <Text type="secondary">
              还没有账户？{' '}
              <Link to="/register">立即注册</Link>
            </Text>
          </div> */}
        </Space>
      </Card>
      </div>
    </>
  );
};

export default LoginPage;
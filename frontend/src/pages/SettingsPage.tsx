import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Avatar,
  Row,
  Col,
  Typography,
  message,
  Space,
  Divider,
  Alert,
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  SaveOutlined,
  SettingOutlined,
  KeyOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/auth';
import { UserService, SystemConfigService } from '../api/services';

const { Title, Text } = Typography;
// const { Option } = Select;

const SettingsPage: React.FC = () => {
  const { user, loadUser } = useAuthStore();
  
  const [activeTab, setActiveTab] = useState<'profile' | 'system'>('profile');
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileForm] = Form.useForm();
  const [systemConfigForm] = Form.useForm();
  
  const [loading, setLoading] = useState(false);
  const [userDataLoaded, setUserDataLoaded] = useState(false);

  // 初始化用户数据和表单
  useEffect(() => {
    const initializeData = async () => {
      try {
        // 如果用户数据不存在或者数据还没有加载过，尝试重新加载
        if (!user && !userDataLoaded) {
          await loadUser();
          setUserDataLoaded(true);
        } else if (user) {
          setUserDataLoaded(true);
        }
      } catch (error) {
        console.error('加载用户数据失败:', error);
        message.error('加载用户数据失败，请刷新页面重试');
      }
    };

    initializeData();
    loadSystemConfig();
  }, [user, loadUser, userDataLoaded]);

  // 当用户数据更新时，设置表单值
  useEffect(() => {
    if (user && userDataLoaded) {
      profileForm.setFieldsValue({
        username: user.username,
        email: user.email,
        full_name: user.full_name,
      });
    }
  }, [user, profileForm, userDataLoaded]);

  const loadSystemConfig = async () => {
    try {
      const config = await SystemConfigService.getDefaultPassword();
      systemConfigForm.setFieldsValue({
        default_password: config.data.default_password,
      });
    } catch (error) {
      message.error('加载系统配置失败');
    }
  };

  // 更新个人资料
  const handleUpdateProfile = async (values: any) => {
    try {
      setLoading(true);
      await UserService.updateProfile(values);
      await loadUser();
      setIsEditingProfile(false);
      message.success('个人资料更新成功');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  // 更新系统配置
  const handleUpdateSystemConfig = async (values: any) => {
    try {
      setLoading(true);
      await SystemConfigService.setDefaultPassword(values.default_password);
      await loadSystemConfig();
      message.success('系统配置更新成功');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新失败');
    } finally {
      setLoading(false);
    }
  };



  const tabContent = {
    profile: (
      <Card title="个人资料" extra={
        <Button
          type="primary"
          icon={<EditOutlined />}
          onClick={() => setIsEditingProfile(!isEditingProfile)}
        >
          {isEditingProfile ? '取消编辑' : '编辑资料'}
        </Button>
      }>
        <Row gutter={24}>
          <Col xs={24} md={8} style={{ textAlign: 'center' }}>
            <Avatar size={120} icon={<UserOutlined />} style={{ marginBottom: 16 }}>
              {user?.full_name?.[0] || user?.username?.[0]}
            </Avatar>
            <div>
              <Title level={4}>{user?.full_name}</Title>
              <Text type="secondary">@{user?.username}</Text>
            </div>
          </Col>
          <Col xs={24} md={16}>
            <Form
              form={profileForm}
              layout="vertical"
              onFinish={handleUpdateProfile}
              disabled={!isEditingProfile}
            >
              <Form.Item
                label="用户名"
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input disabled />
              </Form.Item>
              
              <Form.Item
                label="邮箱"
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input />
              </Form.Item>
              
              <Form.Item
                label="姓名"
                name="full_name"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input />
              </Form.Item>
              
              {isEditingProfile && (
                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<SaveOutlined />}
                    loading={loading}
                  >
                    保存修改
                  </Button>
                </Form.Item>
              )}
            </Form>
          </Col>
        </Row>
      </Card>
    ),



    system: (
      <Card title={
        <Space>
          <KeyOutlined />
          参数管理
        </Space>
      }>
        <Form
          form={systemConfigForm}
          layout="vertical"
          onFinish={handleUpdateSystemConfig}
        >
          <Form.Item
            label="默认密码"
            name="default_password"
            rules={[
              { required: true, message: '请输入默认密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password placeholder="请输入默认密码" />
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
            >
              保存配置
            </Button>
          </Form.Item>
        </Form>
        
        <Divider />
        
        <Alert
          message="配置说明"
          description="新创建的用户将使用此默认密码。建议定期更新默认密码以确保安全。"
          type="info"
          showIcon
        />
      </Card>
    ),
  };

  return (
    <div>
      <Title level={2}>设置</Title>
      
      {/* 标签导航 */}
      <div style={{ marginBottom: 24 }}>
        <Space size="large">
          <Button
            type={activeTab === 'profile' ? 'primary' : 'default'}
            icon={<UserOutlined />}
            onClick={() => setActiveTab('profile')}
          >
            个人资料
          </Button>

          <Button
            type={activeTab === 'system' ? 'primary' : 'default'}
            icon={<SettingOutlined />}
            onClick={() => setActiveTab('system')}
          >
            参数管理
          </Button>
        </Space>
      </div>

      {/* 内容区域 */}
      {tabContent[activeTab]}


    </div>
  );
};

export default SettingsPage;
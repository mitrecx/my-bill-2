import React, { useState, useEffect, useCallback } from 'react';
import {
  Typography,
  Card,
  Row,
  Col,
  Form,
  Input,
  Button,
  Avatar,
  Space,
  Divider,
  Table,
  Tag,
  Modal,
  message,
  Popconfirm,
  Alert,
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  PlusOutlined,
  DeleteOutlined,
  TeamOutlined,
  SettingOutlined,
  SaveOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/auth';
import { UserService, FamilyService } from '../api/services';
import type { Family, FamilyMember } from '../types';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

const SettingsPage: React.FC = () => {
  const { user, loadUser } = useAuthStore();
  
  const [activeTab, setActiveTab] = useState<'profile' | 'family' | 'system'>('profile');
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileForm] = Form.useForm();
  const [familyForm] = Form.useForm();
  
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamily, setSelectedFamily] = useState<Family | null>(null);
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [isFamilyModalVisible, setIsFamilyModalVisible] = useState(false);
  const [isEditingFamily, setIsEditingFamily] = useState(false);
  const [loading, setLoading] = useState(false);
  const [familyLoading, setFamilyLoading] = useState(false);
  const [userLoading, setUserLoading] = useState(false);

  // 使用useCallback来优化函数，避免不必要的重新渲染
  const loadFamilies = useCallback(async () => {
    try {
      setFamilyLoading(true);
      const familiesData = await FamilyService.getFamilies();
      console.log('[SettingsPage] families loaded', familiesData);
      if (familiesData.success && Array.isArray(familiesData.data)) {
        setFamilies(familiesData.data);
      } else {
        setFamilies([]);
      }
    } catch (error) {
      console.error('加载家庭列表失败:', error);
      message.error('加载家庭列表失败');
      setFamilies([]);
    } finally {
      setFamilyLoading(false);
    }
  }, []);

  const loadFamilyMembers = useCallback(async (familyId: number) => {
    try {
      const members = await FamilyService.getFamilyMembers(familyId);
      if (members.success && Array.isArray(members.data)) {
        setFamilyMembers(members.data);
      } else {
        setFamilyMembers([]);
      }
    } catch (error) {
      console.error('加载家庭成员失败:', error);
      message.error('加载家庭成员失败');
      setFamilyMembers([]);
    }
  }, []);

  // 初始化加载用户数据
  useEffect(() => {
    const initializeUser = async () => {
      try {
        setUserLoading(true);
        await loadUser();
      } catch (error) {
        console.error('加载用户数据失败:', error);
        message.error('加载用户数据失败，请刷新页面重试');
      } finally {
        setUserLoading(false);
      }
    };

    initializeUser();
  }, [loadUser]);

  // 当用户数据加载完成后，设置表单值并加载家庭数据
  useEffect(() => {
    if (user) {
      // 设置个人资料表单的初始值
      profileForm.setFieldsValue({
        username: user.username,
        email: user.email,
        full_name: user.full_name,
      });
      
      // 加载家庭数据
      loadFamilies();
    }
  }, [user, profileForm, loadFamilies]);

  // 更新个人资料
  const handleUpdateProfile = async (values: any) => {
    try {
      setLoading(true);
      await UserService.updateProfile(values);
      await loadUser();
      setIsEditingProfile(false);
      message.success('个人资料更新成功');
    } catch (error: any) {
      console.error('更新个人资料失败:', error);
      message.error(error.response?.data?.detail || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建或更新家庭
  const handleSaveFamily = async (values: any) => {
    try {
      setLoading(true);
      
      if (isEditingFamily && selectedFamily) {
        await FamilyService.updateFamily(selectedFamily.id, values);
        message.success('家庭信息更新成功');
      } else {
        await FamilyService.createFamily(values);
        message.success('家庭创建成功');
      }
      
      await loadFamilies();
      setIsFamilyModalVisible(false);
      setIsEditingFamily(false);
      setSelectedFamily(null);
      familyForm.resetFields();
    } catch (error: any) {
      console.error('保存家庭失败:', error);
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除家庭
  const handleDeleteFamily = async (familyId: number) => {
    try {
      setLoading(true);
      await FamilyService.deleteFamily(familyId);
      await loadFamilies();
      
      // 如果删除的是当前选中的家庭，清空选中状态
      if (selectedFamily?.id === familyId) {
        setSelectedFamily(null);
        setFamilyMembers([]);
      }
      
      message.success('家庭删除成功');
    } catch (error: any) {
      console.error('删除家庭失败:', error);
      message.error(error.response?.data?.detail || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  // 查看家庭详情
  const handleViewFamily = async (family: Family) => {
    setSelectedFamily(family);
    await loadFamilyMembers(family.id);
  };

  // 取消编辑个人资料时重置表单
  const handleCancelEditProfile = () => {
    setIsEditingProfile(false);
    if (user) {
      profileForm.setFieldsValue({
        username: user.username,
        email: user.email,
        full_name: user.full_name,
      });
    }
  };

  // 取消家庭模态框
  const handleCancelFamilyModal = () => {
    setIsFamilyModalVisible(false);
    setIsEditingFamily(false);
    setSelectedFamily(null);
    familyForm.resetFields();
  };

  // 家庭表格列定义
  const familyColumns: ColumnsType<Family> = [
    {
      title: '家庭名称',
      dataIndex: 'family_name',
      key: 'family_name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (desc: string) => desc || '无描述',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => {
        try {
          return new Date(date).toLocaleDateString();
        } catch {
          return '无效日期';
        }
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: Family) => (
        <Space size="small">
          <Button
            type="text"
            icon={<TeamOutlined />}
            size="small"
            onClick={() => handleViewFamily(record)}
          >
            成员
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            onClick={() => {
              setSelectedFamily(record);
              setIsEditingFamily(true);
              setIsFamilyModalVisible(true);
              familyForm.setFieldsValue({
                family_name: record.family_name,
                description: record.description,
              });
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除这个家庭吗？"
            description="删除后无法恢复，请谨慎操作。"
            onConfirm={() => handleDeleteFamily(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              icon={<DeleteOutlined />}
              size="small"
              danger
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 家庭成员表格列定义
  const memberColumns: ColumnsType<FamilyMember> = [
    {
      title: '用户名',
      dataIndex: ['user', 'username'],
      key: 'username',
      render: (username: string) => username || '未知用户',
    },
    {
      title: '姓名',
      dataIndex: ['user', 'full_name'],
      key: 'full_name',
      render: (fullName: string) => fullName || '未填写',
    },
    {
      title: '邮箱',
      dataIndex: ['user', 'email'],
      key: 'email',
      render: (email: string) => email || '未填写',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const roleMap = {
          owner: { text: '所有者', color: 'red' },
          admin: { text: '管理员', color: 'orange' },
          member: { text: '成员', color: 'blue' },
        };
        const roleInfo = roleMap[role as keyof typeof roleMap] || { text: role, color: 'default' };
        return <Tag color={roleInfo.color}>{roleInfo.text}</Tag>;
      },
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date: string) => {
        try {
          return new Date(date).toLocaleDateString();
        } catch {
          return '无效日期';
        }
      },
    },
  ];

  const tabContent = {
    profile: (
      <Card 
        title="个人资料" 
        loading={userLoading}
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              if (isEditingProfile) {
                handleCancelEditProfile();
              } else {
                setIsEditingProfile(true);
              }
            }}
          >
            {isEditingProfile ? '取消编辑' : '编辑资料'}
          </Button>
        }
      >
        <Row gutter={24}>
          <Col xs={24} md={8} style={{ textAlign: 'center' }}>
            <Avatar size={120} icon={<UserOutlined />} style={{ marginBottom: 16 }}>
              {user?.full_name?.[0] || user?.username?.[0]}
            </Avatar>
            <div>
              <Title level={4}>{user?.full_name || user?.username || '未知用户'}</Title>
              <Text type="secondary">@{user?.username || 'unknown'}</Text>
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
                  <Space>
                    <Button
                      type="primary"
                      htmlType="submit"
                      icon={<SaveOutlined />}
                      loading={loading}
                    >
                      保存修改
                    </Button>
                    <Button
                      onClick={handleCancelEditProfile}
                    >
                      取消
                    </Button>
                  </Space>
                </Form.Item>
              )}
            </Form>
          </Col>
        </Row>
      </Card>
    ),

    family: (
      <div>
        <Card
          title="家庭管理"
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setSelectedFamily(null);
                setIsEditingFamily(false);
                setIsFamilyModalVisible(true);
                familyForm.resetFields();
              }}
            >
              创建家庭
            </Button>
          }
        >
          <Table
            columns={familyColumns}
            dataSource={families}
            rowKey="id"
            pagination={{ pageSize: 5 }}
            loading={familyLoading || loading}
          />
        </Card>

        {selectedFamily && (
          <Card
            title={`${selectedFamily.family_name} - 成员列表`}
            style={{ marginTop: 16 }}
          >
            {familyMembers.length > 0 ? (
              <Table
                columns={memberColumns}
                dataSource={familyMembers}
                rowKey="id"
                pagination={false}
                size="small"
              />
            ) : (
              <Alert
                message="暂无成员"
                description="该家庭暂无成员信息"
                type="info"
                showIcon
              />
            )}
          </Card>
        )}
      </div>
    ),

    system: (
      <Card title="系统设置">
        <Alert
          message="系统设置"
          description="系统设置功能正在开发中，包括主题设置、通知设置、数据导出等功能。"
          type="info"
          showIcon
        />
        
        <Divider />
        
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={5}>应用信息</Title>
            <Text type="secondary">版本：1.0.0</Text><br />
            <Text type="secondary">构建时间：{new Date().toLocaleDateString()}</Text>
          </div>
          
          <div>
            <Title level={5}>数据管理</Title>
            <Space>
              <Button>导出数据</Button>
              <Button danger>清空缓存</Button>
            </Space>
          </div>
        </Space>
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
            type={activeTab === 'family' ? 'primary' : 'default'}
            icon={<TeamOutlined />}
            onClick={() => setActiveTab('family')}
          >
            家庭管理
          </Button>
          <Button
            type={activeTab === 'system' ? 'primary' : 'default'}
            icon={<SettingOutlined />}
            onClick={() => setActiveTab('system')}
          >
            系统设置
          </Button>
        </Space>
      </div>

      {/* 内容区域 */}
      {tabContent[activeTab]}

      {/* 家庭编辑模态框 */}
      <Modal
        title={isEditingFamily ? '编辑家庭' : '创建家庭'}
        open={isFamilyModalVisible}
        onCancel={handleCancelFamilyModal}
        footer={null}
      >
        <Form
          form={familyForm}
          layout="vertical"
          onFinish={handleSaveFamily}
        >
          <Form.Item
            label="家庭名称"
            name="family_name"
            rules={[{ required: true, message: '请输入家庭名称' }]}
          >
            <Input placeholder="请输入家庭名称" />
          </Form.Item>
          
          <Form.Item
            label="描述"
            name="description"
          >
            <Input.TextArea 
              rows={3}
              placeholder="请输入家庭描述（可选）"
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
              >
                {isEditingFamily ? '更新' : '创建'}
              </Button>
              <Button
                onClick={handleCancelFamilyModal}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SettingsPage;
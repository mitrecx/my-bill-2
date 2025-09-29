import React, { useState, useEffect, useCallback } from 'react';
import {
  Typography,
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useFamilyStore } from '../stores/family';
import type { Family } from '../types';
import { useAuthStore } from '../stores/auth';

const { Title } = Typography;
const { Option } = Select;

interface UserSearchOption {
  value: string;
  label: string;
  id: number;
}

// 防抖函数
const useDebounce = (callback: Function, delay: number) => {
  const [debounceTimer, setDebounceTimer] = useState<number | null>(null);

  const debouncedCallback = useCallback((...args: any[]) => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    const newTimer = setTimeout(() => {
      callback(...args);
    }, delay);
    setDebounceTimer(newTimer);
  }, [callback, delay, debounceTimer]);

  return debouncedCallback;
};

const FamilyManagePage: React.FC = () => {
  const {
    families,
    currentFamily,
    members,
    loading,
    fetchFamilies,
    createFamily,
    updateFamily,
    deleteFamily,
    fetchFamilyMembers,
    leaveFamily,
    searchUsers,
  } = useFamilyStore();
  const { user } = useAuthStore();

  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingFamily, setEditingFamily] = useState<Family | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [userSearchOptions, setUserSearchOptions] = useState<UserSearchOption[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  useEffect(() => {
    fetchFamilies();
  }, [fetchFamilies]);

  useEffect(() => {
    if (currentFamily) {
      fetchFamilyMembers(currentFamily.id);
    }
  }, [currentFamily, fetchFamilyMembers]);

  const handleCreateFamily = async (values: any) => {
    try {
      await createFamily({
        family_name: values.family_name,
        description: values.description,
        invite_usernames: values.invite_usernames || [],
      });
      message.success('家庭创建成功');
      setCreateModalVisible(false);
      createForm.resetFields();
      setUserSearchOptions([]);
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleEditFamily = async (values: any) => {
    if (!editingFamily) return;
    // 再次校验权限，防止通过其他方式触发更新
    if (!canManageFamily(editingFamily)) {
      message.warning('无权限更新该家庭信息');
      return;
    }
    
    try {
      await updateFamily(editingFamily.id, values);
      message.success('家庭信息更新成功');
      setEditModalVisible(false);
      setEditingFamily(null);
      editForm.resetFields();
    } catch (error: any) {
      const status = error?.response?.status;
      const errMsg = status === 404
        ? '更新失败：家庭不存在或无权限'
        : (error?.friendlyMessage || error?.response?.data?.message || error?.response?.data?.detail || '更新失败');
      message.error(errMsg);
    }
  };

  const handleDeleteFamily = async (familyId: number) => {
    try {
      await deleteFamily(familyId);
      message.success('家庭删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleLeaveFamily = async (familyId: number) => {
    try {
      await leaveFamily(familyId);
      message.success('已退出家庭');
    } catch (error) {
      message.error('退出失败');
    }
  };

  const handleUserSearch = async (searchText: string) => {
    if (!searchText || searchText.trim().length < 1) {
      setUserSearchOptions([]);
      return;
    }

    // 如果搜索文本太短，显示提示但不搜索
    if (searchText.trim().length < 2) {
      setUserSearchOptions([]);
      return;
    }

    setSearchLoading(true);
    try {
      const users = await searchUsers(searchText.trim());
      const options = users.map(user => ({
        value: user.username,
        label: `${user.username}${user.full_name ? ` (${user.full_name})` : ''}`,
        id: user.id,
      }));
      setUserSearchOptions(options);
    } catch (error) {
      console.error('搜索用户失败:', error);
      setUserSearchOptions([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // 使用防抖的搜索函数
  const debouncedUserSearch = useDebounce(handleUserSearch, 300);

  const openEditModal = (family: Family) => {
    setEditingFamily(family);
    editForm.setFieldsValue({
      family_name: family.family_name,
      description: family.description,
    });
    setEditModalVisible(true);
  };

  // 仅家庭创建者或该家庭管理员可编辑/删除
  const canManageFamily = (family: Family): boolean => {
    if (!user) return false;
    // 创建者可管理
    if (family.created_by === user.id) return true;
    // 当前家庭且用户为管理员
    if (currentFamily && currentFamily.id === family.id) {
      const me = members.find(m => m.user_id === user.id);
      if (me && me.role === 'admin') return true;
    }
    return false;
  };

  const familyColumns = [
    {
      title: '家庭名称',
      dataIndex: 'family_name',
      key: 'family_name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Family) => (
        <Space>
          {canManageFamily(record) && (
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => openEditModal(record)}
            >
              编辑
            </Button>
          )}
          <Popconfirm
            title="确定要退出这个家庭吗？"
            onConfirm={() => handleLeaveFamily(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" icon={<LogoutOutlined />} danger>
              退出
            </Button>
          </Popconfirm>
          {canManageFamily(record) && (
            <Popconfirm
              title="确定要删除这个家庭吗？此操作不可恢复！"
              onConfirm={() => handleDeleteFamily(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" icon={<DeleteOutlined />} danger>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  const memberColumns = [
    {
      title: '用户名',
      dataIndex: ['user', 'username'],
      key: 'username',
      render: (text: string) => text || '-',
    },
    {
      title: '姓名',
      dataIndex: ['user', 'full_name'],
      key: 'full_name',
      render: (text: string) => text || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>
          {role === 'admin' ? '管理员' : '成员'}
        </Tag>
      ),
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date: string) => (date ? new Date(date).toLocaleDateString() : '-'),
    },
  ];

  return (
    <div style={{ padding: '0 24px' }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
            
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建家庭
            </Button>
          </Space>
        </div>

        <div style={{ marginBottom: 24 }}>
          <Title level={4}>我的家庭</Title>
          <Table
            columns={familyColumns}
            dataSource={families}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </div>

        {currentFamily && (
          <>
            <Divider />
            <div>
              <Title level={4}>家庭成员 - {currentFamily.family_name}</Title>
              <Table
                columns={memberColumns}
                dataSource={members}
                rowKey="id"
                loading={loading}
                pagination={false}
              />
            </div>
          </>
        )}
      </Card>

      {/* 创建家庭模态框 */}
      <Modal
        title="创建家庭"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
          setUserSearchOptions([]);
        }}
        footer={null}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateFamily}
        >
          <Form.Item
            name="family_name"
            label="家庭名称"
            rules={[{ required: true, message: '请输入家庭名称' }]}
          >
            <Input placeholder="请输入家庭名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="请输入家庭描述（可选）" rows={3} />
          </Form.Item>

          <Form.Item
            name="invite_usernames"
            label="邀请成员"
            help="输入至少2个字符开始搜索用户名或姓名"
          >
            <Select
              mode="multiple"
              placeholder="搜索用户名或姓名邀请成员"
              showSearch
              filterOption={false}
              onSearch={debouncedUserSearch}
              loading={searchLoading}
              notFoundContent={searchLoading ? '搜索中...' : '未找到用户'}
              allowClear
              showArrow={false}
            >
              {userSearchOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建
              </Button>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
                setUserSearchOptions([]);
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑家庭模态框 */}
      <Modal
        title="编辑家庭"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingFamily(null);
          editForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditFamily}
        >
          <Form.Item
            name="family_name"
            label="家庭名称"
            rules={[{ required: true, message: '请输入家庭名称' }]}
          >
            <Input placeholder="请输入家庭名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="请输入家庭描述（可选）" rows={3} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                更新
              </Button>
              <Button onClick={() => {
                setEditModalVisible(false);
                setEditingFamily(null);
                editForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FamilyManagePage;
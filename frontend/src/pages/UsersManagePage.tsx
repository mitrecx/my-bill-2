import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Popconfirm, message, Modal, Form, Input, Pagination, Spin, Tag, Switch, Descriptions, Select, Row, Col, Typography } from 'antd';
import { SearchOutlined, EyeOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
const { Text } = Typography;
import { UserService } from '../api/services';
import type { User } from '../types';

interface UserFormValues {
  username?: string;
  password?: string;
  full_name?: string;
  email?: string;
  is_active?: boolean;
}

interface SearchParams {
  username: string;
  full_name: string;
  role: string;
}

const PAGE_SIZE = 10;

const UsersManagePage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'add' | 'edit' | 'view'>('add');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [form] = Form.useForm<UserFormValues>();
  const [confirmLoading, setConfirmLoading] = useState(false);
  
  // 搜索参数
  const [searchParams, setSearchParams] = useState<SearchParams>({
    username: '',
    full_name: '',
    role: ''
  });

  // 加载用户列表
  const fetchUsers = async (pageNum = 1, params = searchParams) => {
    setLoading(true);
    try {
      const queryParams: any = { page: pageNum, size: PAGE_SIZE };
      
      // 只添加非空的搜索参数
      if (params.username.trim()) {
        queryParams.username = params.username.trim();
      }
      if (params.full_name.trim()) {
        queryParams.full_name = params.full_name.trim();
      }
      if (params.role) {
        queryParams.role = params.role;
      }
      
      const res = await UserService.listUsers(queryParams);
      setUsers(res.data.items);
      setTotal(res.data.total);
      setPage(pageNum);
    } catch (err: any) {
      message.error(err?.message || '加载用户失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers(1);
  }, []);

  // 处理搜索
  const handleSearch = () => {
    fetchUsers(1, searchParams);
  };

  // 重置搜索
  const handleReset = () => {
    const resetParams = { username: '', full_name: '', role: '' };
    setSearchParams(resetParams);
    fetchUsers(1, resetParams);
  };

  // 打开添加用户弹窗
  const handleAdd = () => {
    setModalType('add');
    setCurrentUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开查看用户详情弹窗
  const handleView = (user: User) => {
    setModalType('view');
    setCurrentUser(user);
    setModalVisible(true);
  };

  // 打开编辑用户弹窗
  const handleEdit = (user: User) => {
    setModalType('edit');
    setCurrentUser(user);
    form.setFieldsValue({
      full_name: user.full_name,
      email: user.email,
      is_active: user.is_active,
    });
    setModalVisible(true);
  };

  // 删除用户
  const handleDelete = async (id: number) => {
    setLoading(true);
    try {
      await UserService.deleteUser(id);
      message.success('用户已删除');
      fetchUsers(page);
    } catch (err: any) {
      message.error(err?.message || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  // 提交表单（添加/编辑）
  const handleModalOk = async () => {
    if (modalType === 'view') {
      setModalVisible(false);
      return;
    }

    try {
      const values = await form.validateFields();
      setConfirmLoading(true);
      if (modalType === 'add') {
        await UserService.createUser(values as Required<UserFormValues>);
        message.success('用户添加成功');
        fetchUsers(1);
      } else if (modalType === 'edit' && currentUser) {
        await UserService.updateUser(currentUser.id, values);
        message.success('用户更新成功');
        fetchUsers(page);
      }
      setModalVisible(false);
    } catch (err: any) {
      if (err?.errorFields) return; // 表单校验错误
      message.error(err?.message || '操作失败');
    } finally {
      setConfirmLoading(false);
    }
  };

  // 关闭弹窗
  const handleModalCancel = () => {
    setModalVisible(false);
    form.resetFields();
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'full_name', key: 'full_name' },
    { 
      title: '角色', 
      dataIndex: 'is_admin', 
      key: 'is_admin', 
      render: (isAdmin: boolean) => isAdmin ? <Tag color="red">admin</Tag> : <Tag color="default">无</Tag>
    },
    { title: '家庭角色', dataIndex: 'family_role', key: 'family_role', render: (role: string) => role || '未加入家庭' },
    { 
      title: '状态', 
      dataIndex: 'is_active', 
      key: 'is_active', 
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? '正常' : '已禁用'}
        </Tag>
      )
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t && t.slice(0, 19).replace('T', ' ') },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleView(record)}>查看</Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定要删除该用户吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger disabled={record.username === 'admin'}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getModalTitle = () => {
    switch (modalType) {
      case 'add': return '添加用户';
      case 'edit': return '编辑用户';
      case 'view': return '用户详情';
      default: return '';
    }
  };

  const renderModalContent = () => {
    if (modalType === 'view' && currentUser) {
      return (
        <Descriptions column={1} bordered>
          <Descriptions.Item label="用户名">{currentUser.username}</Descriptions.Item>
          <Descriptions.Item label="姓名">{currentUser.full_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{currentUser.email || '-'}</Descriptions.Item>
          <Descriptions.Item label="角色">
            {currentUser.is_admin ? <Tag color="red">admin</Tag> : <Tag color="default">无</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label="家庭">{currentUser.family_name || '未加入家庭'}</Descriptions.Item>
          <Descriptions.Item label="家庭角色">{currentUser.family_role || '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={currentUser.is_active ? 'success' : 'error'}>
              {currentUser.is_active ? '正常' : '已禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {currentUser.created_at && currentUser.created_at.slice(0, 19).replace('T', ' ')}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {currentUser.updated_at && currentUser.updated_at.slice(0, 19).replace('T', ' ')}
          </Descriptions.Item>
        </Descriptions>
      );
    }

    return (
      <Form
        form={form}
        layout="vertical"
        initialValues={{ username: '', password: '', full_name: '', email: '', is_active: true }}
      >
        {modalType === 'add' && (
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }, { min: 2, message: '至少2个字符' }]}
          >
            <Input placeholder="用户名" />
          </Form.Item>
        )}
        {modalType === 'add' && (
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '至少6个字符' }]}
          >
            <Input.Password placeholder="密码" />
          </Form.Item>
        )}
        <Form.Item label="姓名" name="full_name">
          <Input placeholder="姓名" />
        </Form.Item>
        <Form.Item label="邮箱" name="email" rules={[{ type: 'email', message: '邮箱格式不正确' }]}> 
          <Input placeholder="邮箱" />
        </Form.Item>
        {modalType === 'edit' && (
          <Form.Item label="新密码" name="password" rules={[{ min: 6, message: '至少6个字符' }]}> 
            <Input.Password placeholder="如需修改请输入新密码" />
          </Form.Item>
        )}
        {modalType === 'edit' && (
          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="正常" unCheckedChildren="禁用" />
          </Form.Item>
        )}
      </Form>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>用户管理</h2>
      
      {/* 搜索区域 */}
      <div style={{ marginBottom: 16, padding: 16, backgroundColor: '#fafafa', borderRadius: 6 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Space align="center">
              <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>用户名：</Text>
              <Input
                placeholder="用户名"
                value={searchParams.username}
                onChange={(e) => setSearchParams({ ...searchParams, username: e.target.value })}
                allowClear
                style={{ width: '100%' }}
              />
            </Space>
          </Col>
          <Col span={6}>
            <Space align="center">
              <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>姓名：</Text>
              <Input
                placeholder="姓名"
                value={searchParams.full_name}
                onChange={(e) => setSearchParams({ ...searchParams, full_name: e.target.value })}
                allowClear
                style={{ width: '100%' }}
              />
            </Space>
          </Col>
          <Col span={6}>
            <Space align="center">
              <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>角色：</Text>
              <Select
                placeholder="角色"
                value={searchParams.role || undefined}
                onChange={(value) => setSearchParams({ ...searchParams, role: value || '' })}
                allowClear
                style={{ width: '100%' }}
              >
                <Select.Option value="admin">管理员</Select.Option>
                <Select.Option value="user">普通用户</Select.Option>
              </Select>
            </Space>
          </Col>
          <Col span={6} style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                新增
              </Button>
            </Space>
          </Col>
        </Row>

        {/* 操作按钮单独一行：查询/重置 居中 */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 12 }}>
          <Space>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>查询</Button>
            <Button onClick={handleReset}>重置</Button>
          </Space>
        </div>
      </div>

      <Spin spinning={loading}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={users}
          pagination={false}
        />
        <Pagination
          style={{ marginTop: 16, textAlign: 'right' }}
          current={page}
          pageSize={PAGE_SIZE}
          total={total}
          onChange={(page) => fetchUsers(page, searchParams)}
          showSizeChanger={false}
        />
      </Spin>
      <Modal
        title={getModalTitle()}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={confirmLoading}
        destroyOnClose
        okText={modalType === 'view' ? '关闭' : '确定'}
        cancelText={modalType === 'view' ? null : '取消'}
        cancelButtonProps={{ style: modalType === 'view' ? { display: 'none' } : {} }}
      >
        {renderModalContent()}
      </Modal>
    </div>
  );
};

export default UsersManagePage;
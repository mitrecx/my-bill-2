import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Popconfirm, message, Modal, Form, Input, Pagination, Spin, Tag, Switch } from 'antd';
import type { InputRef } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { UserService } from '../api/services';
import type { User } from '../types';

interface UserFormValues {
  username?: string;
  password?: string;
  full_name?: string;
  email?: string;
  is_active?: boolean;
}

const PAGE_SIZE = 10;

const UsersManagePage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'add' | 'edit'>('add');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [form] = Form.useForm<UserFormValues>();
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = React.useRef<InputRef>(null);

  // 加载用户列表
  const fetchUsers = async (pageNum = 1, query = searchQuery) => {
    setLoading(true);
    try {
      const res = await UserService.listUsers({ page: pageNum, size: PAGE_SIZE, search: query });
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
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    fetchUsers(1, query);
  };

  // 打开添加用户弹窗
  const handleAdd = () => {
    setModalType('add');
    setCurrentUser(null);
    form.resetFields();
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
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '姓名', dataIndex: 'full_name', key: 'full_name' },
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
          <Button type="link" onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定要删除该用户吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger disabled={record.username === 'admin'}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <h2>用户管理</h2>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Button type="primary" onClick={handleAdd}>添加用户</Button>
        <Input.Search
          ref={searchInputRef}
          placeholder="搜索用户名或姓名"
          allowClear
          onSearch={handleSearch}
          style={{ width: 240 }}
          enterButton={<Button icon={<SearchOutlined />} />}
        />
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
          onChange={(page) => fetchUsers(page, searchQuery)}
          showSizeChanger={false}
        />
      </Spin>
      <Modal
        title={modalType === 'add' ? '添加用户' : '编辑用户'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={confirmLoading}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ username: '', password: '', full_name: '', email: '', is_active: true }}
        >
          {modalType === 'add' && (
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }, { min: 3, message: '至少3个字符' }]}
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
      </Modal>
    </div>
  );
};

export default UsersManagePage; 
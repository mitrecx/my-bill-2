import React, { useEffect, useState } from 'react';
import { Card, Avatar, Typography, Space, Descriptions, Button, Modal, Form, Input, message } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/auth';
import { UserService } from '../api/services';

const { Title, Text } = Typography;

const PersonalCenterPage: React.FC = () => {
  const { user, loadUser, isAuthenticated, setUser } = useAuthStore();
  const [editOpen, setEditOpen] = useState(false);
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  // 新增：密码修改独立弹窗与表单
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [passwordForm] = Form.useForm();
  const [pwdSubmitting, setPwdSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadUser().catch((err) => {
        console.error('加载用户信息失败:', err);
      });
    }
  }, [isAuthenticated]);

  const openEdit = async () => {
    setEditOpen(true);
    try {
      const resp = await UserService.getProfile();
      const profile = resp.data;
      form.setFieldsValue({
        full_name: profile?.full_name || '',
        email: profile?.email || '',
      });
    } catch (_err: any) {
      // 静默回退到当前缓存的用户数据进行预填，不显示权限或错误提示
      form.setFieldsValue({
        full_name: user?.full_name || '',
        email: user?.email || '',
      });
    }
  };

  // 新增：打开修改密码弹窗
  const openChangePassword = () => {
    setPasswordOpen(true);
    passwordForm.resetFields();
    passwordForm.setFieldsValue({ new_password: '', confirm_password: '' });
  };

  const refreshProfile = async () => {
    try {
      const resp = await UserService.getProfile();
      const profile = resp.data;
      return profile;
    } catch (err) {
      return null;
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload: any = {
        full_name: values.full_name,
        email: values.email,
      };
      setSubmitting(true);
      const resp = await UserService.updateProfile(payload);
      if (resp.success) {
        // 立即用后端返回的最新用户数据刷新全局状态，驱动页面即时更新
        if (resp.data) {
          setUser(resp.data);
        }
        message.success('个人资料更新成功');
        setEditOpen(false);
        // 仍保留一次拉取作为兜底，避免某些字段后端有额外处理
        const p = await refreshProfile();
        if (p) {
          setUser(p);
          form.setFieldsValue({
            full_name: p.full_name || '',
            email: p.email || '',
          });
        } else {
          await loadUser();
        }
      } else {
        message.error(resp.message || '更新失败');
      }
    } catch (err: any) {
      if (err?.errorFields) {
        return;
      }
      const msg = err?.friendlyMessage || err?.response?.data?.message || err?.response?.data?.detail || err?.message || '更新失败，请稍后重试';
      message.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // 新增：处理修改密码提交
  const handleChangePassword = async () => {
    try {
      const values = await passwordForm.validateFields();
      const newPwd = values.new_password;
      const payload: any = { password: newPwd };
      setPwdSubmitting(true);
      const resp = await UserService.updateProfile(payload);
      if (resp.success) {
        message.success('密码修改成功');
        setPasswordOpen(false);
        passwordForm.resetFields();
        await loadUser();
      } else {
        message.error(resp.message || '密码修改失败');
      }
    } catch (err: any) {
      if (err?.errorFields) {
        return; // 表单校验错误
      }

      // 直接呈现后端返回的具体错误信息（优先 detail/message），不再使用统一的“操作被拒绝”提示
      const data = err?.response?.data;
      let backendMsg: string | undefined;

      if (data) {
        if (Array.isArray(data.detail)) {
          // FastAPI/Pydantic 422 错误数组：组合所有详细信息
          backendMsg = data.detail
            .map((d: any) => {
              const loc = Array.isArray(d?.loc) ? d.loc.join('.') : d?.loc;
              const msg = d?.msg || d?.message || '';
              return loc ? `${loc}: ${msg}` : msg;
            })
            .filter(Boolean)
            .join('；');
        } else if (typeof data.detail === 'string') {
          backendMsg = data.detail;
        } else if (typeof data.message === 'string') {
          backendMsg = data.message;
        } else if (typeof data.error === 'string') {
          backendMsg = data.error;
        }
      }

      const finalMsg = backendMsg || err?.message || '密码修改失败，请稍后重试';
      message.error(finalMsg);
    } finally {
      setPwdSubmitting(false);
    }
  };

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Space align="center" size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space align="center" size="large">
              <Avatar size={96} icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }}>
                {user?.full_name?.[0] || user?.username?.[0] || 'U'}
              </Avatar>
              <div>
                <Title level={3} style={{ marginBottom: 4 }}>{user?.full_name || user?.username || '用户'}</Title>
                <Text type="secondary">@{user?.username}</Text>
              </div>
            </Space>
            <Space>
              <Button onClick={openChangePassword}>修改密码</Button>
              <Button type="primary" onClick={openEdit}>编辑资料</Button>
            </Space>
          </Space>

          <Descriptions column={1} bordered size="middle">
            <Descriptions.Item label="用户名">{user?.username || '-'}</Descriptions.Item>
            <Descriptions.Item label="邮箱">{user?.email || '-'}</Descriptions.Item>
            <Descriptions.Item label="姓名">{user?.full_name || '-'}</Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>

      <Modal
        title="编辑个人资料"
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item label="姓名" name="full_name">
            <Input placeholder="请输入姓名" allowClear />
          </Form.Item>
          <Form.Item label="邮箱" name="email" rules={[
            { type: 'email', message: '邮箱格式不正确' },
          ]}>
            <Input placeholder="请输入邮箱" allowClear />
          </Form.Item>
          {/* 注意：已移除所有与密码相关的输入框 */}
        </Form>
      </Modal>

      {/* 新增：修改密码独立弹窗 */}
      <Modal
        title="修改密码"
        open={passwordOpen}
        onCancel={() => setPasswordOpen(false)}
        onOk={handleChangePassword}
        confirmLoading={pwdSubmitting}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={passwordForm} layout="vertical" preserve={false}>
          <Form.Item label="新密码" name="new_password" rules={[
            { required: true, message: '请输入新密码' },
            { min: 6, message: '密码至少需要6个字符' },
          ]}>
            <Input.Password placeholder="请输入新密码" allowClear />
          </Form.Item>
          <Form.Item label="确认密码" name="confirm_password" dependencies={["new_password"]} rules={[
            { required: true, message: '请再次输入新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                const pwd = getFieldValue('new_password');
                if (!pwd || value === pwd) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}>
            <Input.Password placeholder="请再次输入新密码" allowClear />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PersonalCenterPage;
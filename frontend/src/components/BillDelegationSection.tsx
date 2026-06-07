import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { DeleteOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { BillDelegationService } from '../api/services';
import { useAuthStore } from '../stores/auth';
import { useFamilyStore } from '../stores/family';
import type { BillDelegation } from '../types/billDelegation';

const { Paragraph, Text } = Typography;

const BillDelegationSection: React.FC = () => {
  const { user } = useAuthStore();
  const { members, currentFamily, fetchFamilies, fetchFamilyMembers } = useFamilyStore();
  const [loading, setLoading] = useState(false);
  const [granted, setGranted] = useState<BillDelegation[]>([]);
  const [received, setReceived] = useState<BillDelegation[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const granteeOptions = useMemo(() => {
    return members
      .filter((m) => m.user_id !== user?.id)
      .map((m) => ({
        value: m.user_id,
        label: m.user?.full_name || m.user?.username || `用户 ${m.user_id}`,
      }));
  }, [members, user?.id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await BillDelegationService.list();
      setGranted(res.data.granted || []);
      setReceived(res.data.received || []);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载账单授权失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentFamily) {
      fetchFamilies();
    }
  }, [currentFamily, fetchFamilies]);

  useEffect(() => {
    if (currentFamily?.id) {
      fetchFamilyMembers(currentFamily.id);
    }
  }, [currentFamily?.id, fetchFamilyMembers]);

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await BillDelegationService.create({
        grantee_user_id: values.grantee_user_id,
        can_create: values.can_create ?? true,
        can_update: values.can_update ?? true,
        can_delete: values.can_delete ?? false,
      });
      message.success('账单授权已保存');
      setModalOpen(false);
      form.resetFields();
      await loadData();
    } catch (error: any) {
      if (error?.errorFields) {
        return;
      }
      message.error(error.response?.data?.detail || '保存账单授权失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = (record: BillDelegation) => {
    Modal.confirm({
      title: '撤销账单授权',
      content: `确定撤销对「${record.grantee_name || record.grantee_user_id}」的代管授权吗？`,
      okText: '撤销',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true);
          await BillDelegationService.revoke(record.id);
          message.success('授权已撤销');
          await loadData();
        } catch (error: any) {
          message.error(error.response?.data?.detail || '撤销失败');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const permissionTags = (record: BillDelegation) => (
    <Space size={[4, 4]} wrap>
      {record.can_create && <Tag color="green">可录入</Tag>}
      {record.can_update && <Tag color="blue">可修改</Tag>}
      {record.can_delete && <Tag color="red">可删除</Tag>}
    </Space>
  );

  const grantedColumns = [
    {
      title: '被授权成员',
      dataIndex: 'grantee_name',
      key: 'grantee_name',
      render: (_: string, record: BillDelegation) =>
        record.grantee_name || `用户 ${record.grantee_user_id}`,
    },
    {
      title: '权限',
      key: 'permissions',
      render: (_: unknown, record: BillDelegation) => permissionTags(record),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: BillDelegation) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleRevoke(record)}
        >
          撤销
        </Button>
      ),
    },
  ];

  const receivedColumns = [
    {
      title: '授权人',
      dataIndex: 'grantor_name',
      key: 'grantor_name',
      render: (_: string, record: BillDelegation) =>
        record.grantor_name || `用户 ${record.grantor_user_id}`,
    },
    {
      title: '权限',
      key: 'permissions',
      render: (_: unknown, record: BillDelegation) => permissionTags(record),
    },
  ];

  if (!currentFamily) {
    return (
      <Card>
        <Alert
          type="info"
          showIcon
          message="请先加入家庭"
          description="账单代管授权仅适用于同一家庭成员之间。"
        />
      </Card>
    );
  }

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Paragraph type="secondary" style={{ marginBottom: 8 }}>
            授权家庭成员代管你的账单：对方可在账单页为你录入、修改或删除账单（按勾选权限）。
          </Paragraph>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
              新增授权
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
              刷新
            </Button>
          </Space>
        </div>

        <div>
          <Text strong>我授予他人的授权</Text>
          <Table
            style={{ marginTop: 8 }}
            rowKey="id"
            size="small"
            loading={loading}
            dataSource={granted}
            columns={grantedColumns}
            pagination={false}
            locale={{ emptyText: '暂无授权记录' }}
          />
        </div>

        <div>
          <Text strong>他人授予我的授权</Text>
          <Table
            style={{ marginTop: 8 }}
            rowKey="id"
            size="small"
            loading={loading}
            dataSource={received}
            columns={receivedColumns}
            pagination={false}
            locale={{ emptyText: '暂无收到的授权' }}
          />
        </div>
      </Space>

      <Modal
        title="新增账单授权"
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
        }}
        onOk={handleSave}
        confirmLoading={loading}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            can_create: true,
            can_update: true,
            can_delete: false,
          }}
        >
          <Form.Item
            label="被授权成员"
            name="grantee_user_id"
            rules={[{ required: true, message: '请选择家庭成员' }]}
          >
            <Select
              placeholder="选择要授权的家庭成员"
              options={granteeOptions}
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item label="权限" required>
            <Form.Item name="can_create" valuePropName="checked" noStyle>
              <Checkbox>允许代录账单</Checkbox>
            </Form.Item>
            <Form.Item name="can_update" valuePropName="checked" noStyle>
              <Checkbox style={{ marginLeft: 16 }}>允许修改账单</Checkbox>
            </Form.Item>
            <Form.Item name="can_delete" valuePropName="checked" noStyle>
              <Checkbox style={{ marginLeft: 16 }}>允许删除账单</Checkbox>
            </Form.Item>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default BillDelegationSection;

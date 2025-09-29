import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Button, message, Space, Divider, Alert } from 'antd';
import { SaveOutlined, KeyOutlined } from '@ant-design/icons';
import { SystemConfigService } from '../api/services';

const SettingsPage: React.FC = () => {
  const [systemConfigForm] = Form.useForm();
  const [loading, setLoading] = useState(false);

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

  useEffect(() => {
    loadSystemConfig();
  }, []);

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

  return (
    <div>
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
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
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
    </div>
  );
};

export default SettingsPage;
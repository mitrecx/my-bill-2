import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Input,
  Modal,
  Space,
  Tag,
  Typography,
  message,
  Divider,
  List,
} from 'antd';
import {
  ApiOutlined,
  CopyOutlined,
  KeyOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { McpService } from '../api/services';
import type { McpApiKeyStatus, McpServerInfo } from '../types/mcp';

const { Paragraph, Text, Title } = Typography;

const McpSettingsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [keyStatus, setKeyStatus] = useState<McpApiKeyStatus | null>(null);
  const [serverInfo, setServerInfo] = useState<McpServerInfo | null>(null);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [showKeyModal, setShowKeyModal] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsRes, infoRes] = await Promise.all([
        McpService.getSettings(),
        McpService.getServerInfo(),
      ]);
      setKeyStatus(settingsRes.data);
      setServerInfo(infoRes.data);
    } catch {
      message.error('加载 MCP 设置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateKey = async () => {
    try {
      setLoading(true);
      const res = await McpService.generateApiKey();
      setNewApiKey(res.data.api_key);
      setShowKeyModal(true);
      await loadData();
      message.success('MCP API Key 已生成');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '生成 API Key 失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async () => {
    Modal.confirm({
      title: '确认撤销 MCP API Key？',
      content: '撤销后，所有使用该 Key 的 MCP 客户端将无法连接。',
      okText: '撤销',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true);
          await McpService.revokeApiKey();
          setNewApiKey(null);
          await loadData();
          message.success('MCP API Key 已撤销');
        } catch (error: any) {
          message.error(error.response?.data?.detail || '撤销失败');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const copyText = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      message.success(`${label}已复制`);
    } catch {
      message.error('复制失败');
    }
  };

  const cursorConfigText = serverInfo
    ? JSON.stringify(serverInfo.cursor_config_example, null, 2)
    : '';

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        <ApiOutlined /> MCP 设置
      </Title>

      <Card title="API Key 管理" loading={loading} style={{ marginBottom: 16 }}>
        {keyStatus?.has_key ? (
          <>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="Key 前缀">
                <Text code>{keyStatus.key_prefix}...</Text>
              </Descriptions.Item>
              <Descriptions.Item label="名称">{keyStatus.name || 'default'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{keyStatus.created_at || '-'}</Descriptions.Item>
              <Descriptions.Item label="最近使用">{keyStatus.last_used_at || '尚未使用'}</Descriptions.Item>
            </Descriptions>
            <Space style={{ marginTop: 16 }}>
              <Button type="primary" icon={<ReloadOutlined />} onClick={handleGenerateKey} loading={loading}>
                重新生成
              </Button>
              <Button danger icon={<DeleteOutlined />} onClick={handleRevokeKey} loading={loading}>
                撤销 Key
              </Button>
            </Space>
          </>
        ) : (
          <>
            <Alert
              type="warning"
              showIcon
              message="尚未配置 MCP API Key"
              description="生成 API Key 后，可在 Cursor 等 MCP 客户端中连接家庭账单服务。"
              style={{ marginBottom: 16 }}
            />
            <Button type="primary" icon={<KeyOutlined />} onClick={handleGenerateKey} loading={loading}>
              生成 API Key
            </Button>
          </>
        )}
      </Card>

      <Card title="MCP Server 信息" loading={loading} style={{ marginBottom: 16 }}>
        {serverInfo && (
          <>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="服务名称">{serverInfo.server_name}</Descriptions.Item>
              <Descriptions.Item label="MCP 地址">
                <Space>
                  <Text code>{serverInfo.mcp_url}</Text>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyText(serverInfo.mcp_url, 'MCP 地址')}
                  />
                </Space>
              </Descriptions.Item>
            </Descriptions>

            <Divider orientation="left">可用工具</Divider>
            <List
              size="small"
              bordered
              dataSource={[
                { name: 'create_bill', desc: '单条账单录入' },
                { name: 'create_bills_batch', desc: '批量账单录入' },
                { name: 'query_bills_batch', desc: '批量账单查询（支持多条件筛选）' },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <Space>
                    <Tag color="blue">{item.name}</Tag>
                    <Text>{item.desc}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </>
        )}
      </Card>

      <Card title="Cursor 配置示例">
        <Paragraph type="secondary">
          在 Cursor 的 MCP 配置中添加以下内容（将 YOUR_MCP_API_KEY 替换为生成的 Key）：
        </Paragraph>
        <Input.TextArea
          value={cursorConfigText}
          readOnly
          autoSize={{ minRows: 8, maxRows: 16 }}
          style={{ fontFamily: 'monospace', marginBottom: 12 }}
        />
        <Button icon={<CopyOutlined />} onClick={() => copyText(cursorConfigText, '配置示例')}>
          复制配置
        </Button>
      </Card>

      <Modal
        title="请保存 MCP API Key"
        open={showKeyModal}
        onCancel={() => setShowKeyModal(false)}
        footer={[
          <Button key="copy" type="primary" icon={<CopyOutlined />} onClick={() => newApiKey && copyText(newApiKey, 'API Key')}>
            复制 Key
          </Button>,
          <Button key="close" onClick={() => setShowKeyModal(false)}>
            我已保存
          </Button>,
        ]}
        closable={false}
        maskClosable={false}
      >
        <Alert
          type="error"
          showIcon
          message="此 Key 仅显示一次，关闭后将无法再次查看"
          style={{ marginBottom: 12 }}
        />
        <Input.TextArea value={newApiKey || ''} readOnly autoSize={{ minRows: 3 }} style={{ fontFamily: 'monospace' }} />
      </Modal>
    </div>
  );
};

export default McpSettingsPage;

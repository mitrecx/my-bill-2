import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Badge,
  Button,
  Space,
  Typography,
  Tag,
  Modal,
  message,
  Pagination,
  Empty,
  Spin,
} from 'antd';
import {
  MessageOutlined,
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useMessageStore } from '../stores/message';
import type { Message } from '../types/message';

const { Text, Paragraph } = Typography;
const { confirm } = Modal;

const MessagesPage: React.FC = () => {
  const {
    messages,
    loading,
    total,
    page,
    pageSize,
    unreadCount,
    fetchMessages,
    markAsRead,
    createMessageAction,
    deleteMessage,
  } = useMessageStore();

  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const handleMarkAsRead = async (messageId: number) => {
    try {
      await markAsRead(messageId);
      message.success('已标记为已读');
    } catch (error) {
      message.error('标记失败');
    }
  };

  const handleMessageAction = async (messageId: number, actionType: string) => {
    setActionLoading(messageId);
    try {
      await createMessageAction(messageId, actionType);
      
      if (actionType === 'accept') {
        message.success('已接受邀请');
      } else if (actionType === 'reject') {
        message.success('已拒绝邀请');
      }
      
      // 刷新消息列表
      await fetchMessages();
    } catch (error) {
      message.error('操作失败');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteMessage = (messageId: number) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这条消息吗？',
      onOk: async () => {
        try {
          await deleteMessage(messageId);
          message.success('删除成功');
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handlePageChange = (newPage: number, newPageSize?: number) => {
    fetchMessages(newPage, newPageSize);
  };

  const getMessageTypeTag = (type: string) => {
    switch (type) {
      case 'SYSTEM':
        return <Tag color="blue">系统消息</Tag>;
      case 'FAMILY_INVITE':
        return <Tag color="green">家庭邀请</Tag>;
      default:
        return <Tag>{type}</Tag>;
    }
  };

  const renderMessageActions = (msg: Message) => {
    if (msg.message_type === 'FAMILY_INVITE' && msg.data?.family_id) {
      return (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            loading={actionLoading === msg.id}
            onClick={() => handleMessageAction(msg.id, 'accept')}
          >
            接受
          </Button>
          <Button
            size="small"
            icon={<CloseOutlined />}
            loading={actionLoading === msg.id}
            onClick={() => handleMessageAction(msg.id, 'reject')}
          >
            拒绝
          </Button>
        </Space>
      );
    }
    return null;
  };

  const renderMessageItem = (msg: Message) => (
    <List.Item
      key={msg.id}
      actions={[
        !msg.is_read && (
          <Button
            type="link"
            size="small"
            onClick={() => handleMarkAsRead(msg.id)}
          >
            标记已读
          </Button>
        ),
        <Button
          type="link"
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteMessage(msg.id)}
        >
          删除
        </Button>,
      ].filter(Boolean)}
    >
      <List.Item.Meta
        avatar={
          <Badge dot={!msg.is_read}>
            <MessageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          </Badge>
        }
        title={
          <Space>
            <Text strong={!msg.is_read}>{msg.title}</Text>
            {getMessageTypeTag(msg.message_type)}
            {!msg.is_read && <Badge status="processing" text="未读" />}
          </Space>
        }
        description={
          <div>
            <Paragraph ellipsis={{ rows: 2 }}>{msg.content}</Paragraph>
            <Space>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {new Date(msg.created_at).toLocaleString()}
              </Text>
              {msg.sender_id && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  发送者ID: {msg.sender_id}
                </Text>
              )}
            </Space>
            {renderMessageActions(msg)}
          </div>
        }
      />
    </List.Item>
  );

  return (
    <div style={{ padding: '0 24px' }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Space align="center">
            
            {unreadCount > 0 && (
              <Badge count={unreadCount} style={{ backgroundColor: '#f5222d' }} />
            )}
          </Space>
        </div>

        <Spin spinning={loading}>
          {messages.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无消息"
            />
          ) : (
            <>
              <List
                itemLayout="vertical"
                dataSource={messages}
                renderItem={renderMessageItem}
              />
              
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={total}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total, range) =>
                    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                  }
                  onChange={handlePageChange}
                />
              </div>
            </>
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default MessagesPage;
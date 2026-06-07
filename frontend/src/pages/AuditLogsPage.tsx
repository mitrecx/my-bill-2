import React, { useCallback, useEffect, useState } from 'react';
import {
  Card,
  Table,
  Tag,
  Select,
  Space,
  Typography,
  Button,
  Modal,
  Descriptions,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { AuditService } from '../api/services';
import type { AuditLog } from '../types/audit';

const { Title, Text } = Typography;

const ACTION_LABELS: Record<string, string> = {
  create: '新增',
  update: '修改',
  delete: '删除',
};

const ACTION_COLORS: Record<string, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
};

const SOURCE_LABELS: Record<string, string> = {
  rest: '网页',
  mcp: 'MCP',
  upload: '导入',
  service: '系统',
};

const FIELD_LABELS: Record<string, string> = {
  amount: '金额',
  transaction_type: '交易类型',
  transaction_desc: '交易描述',
  category_id: '分类',
  remark: '备注',
  transaction_time: '交易时间',
  source_type: '来源',
  source_filename: '来源文件',
  currency: '货币',
  user_id: '归属用户',
};

const formatFieldValue = (value: unknown): string => {
  if (value == null || value === '') return '-';
  if (typeof value === 'number') return String(value);
  return String(value);
};

const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [actionFilter, setActionFilter] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [detailLog, setDetailLog] = useState<AuditLog | null>(null);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await AuditService.listAuditLogs({
        entity_type: 'bill',
        action: actionFilter,
        page,
        size: pageSize,
      });
      if (response.success && response.data) {
        setLogs(response.data.items);
        setTotal(response.data.total);
      } else {
        throw new Error(response.message || '获取审计日志失败');
      }
    } catch (error: any) {
      message.error(error?.message || '获取审计日志失败');
      setLogs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [actionFilter, page, pageSize]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const columns: ColumnsType<AuditLog> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 170,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 80,
      render: (value: string) => (
        <Tag color={ACTION_COLORS[value] || 'default'}>{ACTION_LABELS[value] || value}</Tag>
      ),
    },
    {
      title: '账单 ID',
      dataIndex: 'entity_id',
      width: 90,
    },
    {
      title: '操作人',
      dataIndex: 'actor_username',
      width: 120,
      render: (value: string | null) => value || '-',
    },
    {
      title: '账单归属',
      dataIndex: 'target_username',
      width: 120,
      render: (value: string | null) => value || '-',
    },
    {
      title: '来源',
      dataIndex: 'source',
      width: 90,
      render: (value: string) => SOURCE_LABELS[value] || value,
    },
    {
      title: '变更摘要',
      key: 'summary',
      render: (_: unknown, record: AuditLog) => {
        if (record.action === 'create') {
          const amount = record.new_data?.amount;
          return amount != null ? `新增金额 ¥${formatFieldValue(amount)}` : '新增账单';
        }
        if (record.action === 'delete') {
          const amount = record.old_data?.amount;
          return amount != null ? `删除金额 ¥${formatFieldValue(amount)}` : '删除账单';
        }
        const fields = record.changed_fields ? Object.keys(record.changed_fields) : [];
        if (fields.length === 0) return '-';
        return fields.map((field) => FIELD_LABELS[field] || field).join('、');
      },
    },
    {
      title: '详情',
      key: 'detail',
      width: 80,
      render: (_: unknown, record: AuditLog) => (
        <Button type="link" size="small" onClick={() => setDetailLog(record)}>
          查看
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>审计日志</Title>
        <Space>
          <Text type="secondary">操作类型</Text>
          <Select
            allowClear
            placeholder="全部"
            style={{ width: 120 }}
            value={actionFilter}
            onChange={(value) => {
              setActionFilter(value);
              setPage(1);
            }}
            options={[
              { value: 'create', label: '新增' },
              { value: 'update', label: '修改' },
              { value: 'delete', label: '删除' },
            ]}
          />
        </Space>
      </div>

      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={logs}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showTotal: (count) => `共 ${count} 条`,
          onChange: (nextPage, nextSize) => {
            setPage(nextPage);
            setPageSize(nextSize);
          },
        }}
      />

      <Modal
        title="审计详情"
        open={!!detailLog}
        footer={null}
        width={720}
        onCancel={() => setDetailLog(null)}
      >
        {detailLog && (
          <>
            <Descriptions column={2} size="small" bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="时间">
                {dayjs(detailLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="操作">
                {ACTION_LABELS[detailLog.action] || detailLog.action}
              </Descriptions.Item>
              <Descriptions.Item label="账单 ID">{detailLog.entity_id}</Descriptions.Item>
              <Descriptions.Item label="来源">
                {SOURCE_LABELS[detailLog.source] || detailLog.source}
              </Descriptions.Item>
              <Descriptions.Item label="操作人">{detailLog.actor_username || '-'}</Descriptions.Item>
              <Descriptions.Item label="账单归属">{detailLog.target_username || '-'}</Descriptions.Item>
            </Descriptions>

            {detailLog.changed_fields && Object.keys(detailLog.changed_fields).length > 0 && (
              <Table
                size="small"
                pagination={false}
                rowKey={(row) => row.field}
                dataSource={Object.entries(detailLog.changed_fields).map(([field, change]) => ({
                  field,
                  label: FIELD_LABELS[field] || field,
                  oldValue: formatFieldValue(change?.old),
                  newValue: formatFieldValue(change?.new),
                }))}
                columns={[
                  { title: '字段', dataIndex: 'label', width: 120 },
                  { title: '变更前', dataIndex: 'oldValue' },
                  { title: '变更后', dataIndex: 'newValue' },
                ]}
              />
            )}

            {detailLog.action === 'create' && detailLog.new_data && (
              <pre style={{ marginTop: 16, background: '#fafafa', padding: 12, borderRadius: 6, overflow: 'auto' }}>
                {JSON.stringify(detailLog.new_data, null, 2)}
              </pre>
            )}

            {detailLog.action === 'delete' && detailLog.old_data && (
              <pre style={{ marginTop: 16, background: '#fafafa', padding: 12, borderRadius: 6, overflow: 'auto' }}>
                {JSON.stringify(detailLog.old_data, null, 2)}
              </pre>
            )}
          </>
        )}
      </Modal>
    </Card>
  );
};

export default AuditLogsPage;

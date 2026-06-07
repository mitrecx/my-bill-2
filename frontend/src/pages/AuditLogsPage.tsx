import React, { useCallback, useEffect, useMemo, useState } from 'react';
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
import { AuditService, BillService } from '../api/services';
import type { AuditLog } from '../types/audit';
import type { BillCategory } from '../types';

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

const SOURCE_TYPE_LABELS: Record<string, string> = {
  alipay: '支付宝',
  wechat: '微信',
  jd: '京东',
  cmb: '招商银行',
  meituan: '美团',
  manual: '手动录入',
};

const FIELD_LABELS: Record<string, string> = {
  amount: '金额',
  transaction_type: '交易类型',
  transaction_desc: '交易描述',
  category_id: '分类',
  remark: '备注',
  transaction_time: '交易时间',
  source_type: '来源类型',
  source_filename: '来源文件',
  currency: '货币',
  user_id: '归属用户',
};

const BILL_INFO_FIELDS = [
  'transaction_desc',
  'amount',
  'transaction_time',
  'transaction_type',
  'category_id',
  'remark',
  'source_type',
] as const;

const getBillSnapshot = (log: AuditLog): Record<string, unknown> | null => {
  if (log.action === 'delete') return log.old_data || null;
  return log.new_data || log.old_data || null;
};

const formatAuditFieldValue = (
  field: string,
  value: unknown,
  categoryMap: Map<number, string>,
): string => {
  if (value == null || value === '') return '-';
  if (field === 'category_id') {
    const id = Number(value);
    if (!Number.isFinite(id)) return String(value);
    return categoryMap.get(id) || `未知分类 (#${id})`;
  }
  if (field === 'amount') {
    const num = Number(value);
    if (!Number.isFinite(num)) return String(value);
    return `¥${num.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
  }
  if (field === 'transaction_time') {
    const parsed = dayjs(String(value));
    return parsed.isValid() ? parsed.format('YYYY-MM-DD HH:mm:ss') : String(value);
  }
  if (field === 'source_type') {
    const key = String(value);
    return SOURCE_TYPE_LABELS[key] || key;
  }
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
  const [categoryMap, setCategoryMap] = useState<Map<number, string>>(new Map());

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await BillService.getCategories();
        if (response.success && Array.isArray(response.data)) {
          const map = new Map<number, string>();
          (response.data as BillCategory[]).forEach((category) => {
            map.set(category.id, category.name);
          });
          setCategoryMap(map);
        }
      } catch (error) {
        console.error('加载分类失败:', error);
      }
    };
    loadCategories();
  }, []);

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

  const formatValue = useCallback(
    (field: string, value: unknown) => formatAuditFieldValue(field, value, categoryMap),
    [categoryMap],
  );

  const detailBillSnapshot = useMemo(
    () => (detailLog ? getBillSnapshot(detailLog) : null),
    [detailLog],
  );

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
      title: '描述',
      key: 'desc',
      ellipsis: true,
      render: (_: unknown, record: AuditLog) => {
        const snapshot = getBillSnapshot(record);
        const desc = snapshot?.transaction_desc;
        return desc ? String(desc) : '-';
      },
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
          return amount != null ? `新增 ${formatValue('amount', amount)}` : '新增账单';
        }
        if (record.action === 'delete') {
          const amount = record.old_data?.amount;
          return amount != null ? `删除 ${formatValue('amount', amount)}` : '删除账单';
        }
        const fields = record.changed_fields ? Object.keys(record.changed_fields) : [];
        if (fields.length === 0) return '-';
        return fields
          .map((field) => {
            const change = record.changed_fields?.[field];
            if (field === 'category_id' && change) {
              return `${FIELD_LABELS[field]}: ${formatValue(field, change.old)} → ${formatValue(field, change.new)}`;
            }
            return FIELD_LABELS[field] || field;
          })
          .join('、');
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
        width={760}
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

            {detailBillSnapshot && (
              <Descriptions
                title="账单信息"
                column={1}
                size="small"
                bordered
                style={{ marginBottom: 16 }}
              >
                {BILL_INFO_FIELDS.map((field) => {
                  const value = detailBillSnapshot[field];
                  if (value == null || value === '') return null;
                  return (
                    <Descriptions.Item key={field} label={FIELD_LABELS[field]}>
                      {formatValue(field, value)}
                    </Descriptions.Item>
                  );
                })}
              </Descriptions>
            )}

            {detailLog.changed_fields && Object.keys(detailLog.changed_fields).length > 0 && (
              <Table
                size="small"
                pagination={false}
                rowKey={(row) => row.field}
                dataSource={Object.entries(detailLog.changed_fields).map(([field, change]) => ({
                  field,
                  label: FIELD_LABELS[field] || field,
                  oldValue: formatValue(field, change?.old),
                  newValue: formatValue(field, change?.new),
                }))}
                columns={[
                  { title: '字段', dataIndex: 'label', width: 120 },
                  { title: '变更前', dataIndex: 'oldValue' },
                  { title: '变更后', dataIndex: 'newValue' },
                ]}
              />
            )}
          </>
        )}
      </Modal>
    </Card>
  );
};

export default AuditLogsPage;

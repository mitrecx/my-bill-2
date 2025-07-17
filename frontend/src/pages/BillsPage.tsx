import React, { useEffect, useState } from 'react';
import {
  Typography,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Card,
  Tag,
  Modal,
  Form,
  message,
  Popconfirm,
} from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
// import { useAuthStore } from '../stores/auth';
import type { Bill, BillQueryParams } from '../types';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const BillsPage: React.FC = () => {
  // const { user } = useAuthStore();
  const {
    bills,
    categories,
    pagination,
    queryParams,
    isLoading,
    // error,
    fetchBills,
    fetchCategories,
    deleteBill,
    setQueryParams,
  } = useBillsStore();

  const [searchText, setSearchText] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingBill, setEditingBill] = useState<Bill | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchBills();
    fetchCategories();
  }, [fetchBills, fetchCategories]);

  // 处理搜索
  const handleSearch = () => {
    setQueryParams({
      search: searchText,
      page: 1,
    });
    fetchBills();
  };

  // 处理筛选
  const handleFilter = (key: keyof BillQueryParams, value: any) => {
    setQueryParams({
      [key]: value,
      page: 1,
    });
    fetchBills();
  };

  // 处理分页
  const handlePageChange = (page: number, size: number) => {
    setQueryParams({ page, size });
    fetchBills();
  };

  // 处理删除
  const handleDelete = async (id: number) => {
    try {
      await deleteBill(id);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 重置筛选
  const handleReset = () => {
    setSearchText('');
    setQueryParams({
      page: 1,
      size: 20,
      sort_by: 'transaction_date',
      sort_order: 'desc',
    });
    fetchBills();
  };

  // 表格列定义
  const columns: ColumnsType<Bill> = [
    {
      title: '交易时间',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
      sorter: true,
    },
    {
      title: '交易描述',
      dataIndex: 'transaction_desc',
      key: 'transaction_desc',
      ellipsis: true,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: Bill) => (
        <span style={{
          color: record.transaction_type === 'income' ? '#3f8600' : 
                record.transaction_type === 'expense' ? '#cf1322' : '#666',
          fontWeight: 'bold',
        }}>
          {record.transaction_type === 'income' ? '+' : 
           record.transaction_type === 'expense' ? '-' : ''}
          {amount.toFixed(2)}
        </span>
      ),
      sorter: true,
    },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'income' ? 'green' : type === 'expense' ? 'red' : 'blue'}>
          {type === 'income' ? '收入' : type === 'expense' ? '支出' : '不计收支'}
        </Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 100,
      render: (source: string) => {
        const sourceMap = {
          alipay: '支付宝',
          jd: '京东',
          cmb: '招商银行',
        };
        return sourceMap[source as keyof typeof sourceMap] || source;
      },
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: any) => category?.name || '未分类',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record: Bill) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            onClick={() => {
              setEditingBill(record);
              setIsModalVisible(true);
            }}
          />
          <Popconfirm
            title="确定删除这条账单吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              icon={<DeleteOutlined />}
              size="small"
              danger
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <Title level={2} style={{ margin: 0 }}>
          账单管理
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingBill(null);
            setIsModalVisible(true);
          }}
        >
          新增账单
        </Button>
      </div>

      {/* 筛选区域 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索交易描述"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 200 }}
            enterButton={<SearchOutlined />}
          />
          
          <Select
            placeholder="交易类型"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => handleFilter('transaction_type', value)}
            value={queryParams.transaction_type}
          >
            <Option value="income">收入</Option>
            <Option value="expense">支出</Option>
            <Option value="transfer">不计收支</Option>
          </Select>

          <Select
            placeholder="来源"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => handleFilter('source_type', value)}
            value={queryParams.source_type}
          >
            <Option value="alipay">支付宝</Option>
            <Option value="jd">京东</Option>
            <Option value="cmb">招商银行</Option>
          </Select>

          <Select
            placeholder="分类"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => handleFilter('category_id', value)}
            value={queryParams.category_id}
          >
            {categories.map(category => (
              <Option key={category.id} value={category.id}>
                {category.name}
              </Option>
            ))}
          </Select>

          <RangePicker
            placeholder={['开始日期', '结束日期']}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                handleFilter('start_date', dates[0].format('YYYY-MM-DD'));
                handleFilter('end_date', dates[1].format('YYYY-MM-DD'));
              } else {
                handleFilter('start_date', undefined);
                handleFilter('end_date', undefined);
              }
            }}
          />

          <Button onClick={handleReset}>
            重置
          </Button>

          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchBills()}
          >
            刷新
          </Button>
        </Space>
      </Card>

      {/* 账单表格 */}
      <Table
        columns={columns}
        dataSource={bills}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: pagination.page,
          pageSize: pagination.size,
          total: pagination.total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: handlePageChange,
          onShowSizeChange: handlePageChange,
        }}
        onChange={(_paginationInfo, _filters, sorter) => {
          if (Array.isArray(sorter)) return;
          if (sorter.field && sorter.order) {
            setQueryParams({
              sort_by: sorter.field as string,
              sort_order: sorter.order === 'ascend' ? 'asc' : 'desc',
            });
            fetchBills();
          }
        }}
        scroll={{ x: 800 }}
      />

      {/* 编辑/新增模态框 */}
      <Modal
        title={editingBill ? '编辑账单' : '新增账单'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <div style={{ padding: '20px 0' }}>
          账单编辑功能开发中...
        </div>
      </Modal>
    </div>
  );
};

export default BillsPage;
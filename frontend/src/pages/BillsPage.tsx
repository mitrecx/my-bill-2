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
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
import type { Bill, BillListQueryParams } from '../types';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const BillsPage: React.FC = () => {
  const {
    bills,
    categories,
    pagination,
    queryParams,
    isLoading,
    fetchBills,
    fetchCategories,
    deleteBill,
    createBill,
    updateBill,
    setQueryParams,
  } = useBillsStore();

  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
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
  const handleFilter = (key: keyof BillListQueryParams, value: any) => {
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

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingBill) {
        // 更新账单
        await updateBill(editingBill.id, values);
        message.success('更新成功');
      } else {
        // 创建账单 - 添加必要字段
        const createData = {
          ...values,
          transaction_time: values.transaction_time || new Date(),
          source_type: values.source_type || 'manual',
        };
        await createBill(createData);
        message.success('创建成功');
      }
      
      setIsModalVisible(false);
      form.resetFields();
      fetchBills(); // 刷新列表
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(error.message || '操作失败');
    }
  };

  // 重置筛选 - 清空所有搜索条件
  const handleReset = () => {
    setSearchText('');
    setDateRange(null);
    setQueryParams({
      page: 1,
      size: 20,
      sort_by: 'transaction_date',
      sort_order: 'desc',
      search: undefined,
      transaction_type: undefined,
      source_type: undefined,
      category_id: undefined,
      start_date: undefined,
      end_date: undefined,
    });
    fetchBills();
  };

  // 查询按钮 - 触发搜索
  const handleQuery = () => {
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
          <Input
            placeholder="搜索交易描述"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 200 }}
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
            value={dateRange}
            onChange={(dates) => {
              setDateRange(dates);
              if (dates && dates[0] && dates[1]) {
                setQueryParams({
                  start_date: dates[0].format('YYYY-MM-DD'),
                  end_date: dates[1].format('YYYY-MM-DD'),
                  page: 1,
                });
              } else {
                setQueryParams({
                  start_date: undefined,
                  end_date: undefined,
                  page: 1,
                });
              }
            }}
          />

          <Button type="primary" onClick={handleQuery}>
            查询
          </Button>

          <Button onClick={handleReset}>
            重置
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
        footer={[
          <Button key="cancel" onClick={() => {
            setIsModalVisible(false);
            form.resetFields();
          }}>
            取消
          </Button>,
          <Button key="submit" type="primary" onClick={handleSubmit} loading={isLoading}>
            {editingBill ? '更新' : '创建'}
          </Button>,
        ]}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={editingBill ? {
            amount: editingBill.amount,
            transaction_type: editingBill.transaction_type,
            transaction_desc: editingBill.transaction_desc,
            category_id: editingBill.category_id,
            remark: editingBill.raw_data?.remark || '',
          } : {
            transaction_time: new Date(),
            source_type: 'manual',
          }}
        >
          {!editingBill && (
            <Form.Item
              label="交易时间"
              name="transaction_time"
              rules={[{ required: true, message: '请选择交易时间' }]}
            >
              <DatePicker
                showTime
                style={{ width: '100%' }}
                placeholder="请选择交易时间"
              />
            </Form.Item>
          )}

          <Form.Item
            label="金额"
            name="amount"
            rules={[{ required: true, message: '请输入金额' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入金额"
              precision={2}
              min={0}
            />
          </Form.Item>

          <Form.Item
            label="交易类型"
            name="transaction_type"
            rules={[{ required: true, message: '请选择交易类型' }]}
          >
            <Select placeholder="请选择交易类型">
              <Option value="income">收入</Option>
              <Option value="expense">支出</Option>
              <Option value="transfer">不计收支</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="交易描述"
            name="transaction_desc"
            rules={[{ required: true, message: '请输入交易描述' }]}
          >
            <Input placeholder="请输入交易描述" />
          </Form.Item>

          <Form.Item
            label="分类"
            name="category_id"
          >
            <Select placeholder="请选择分类" allowClear>
              {categories.map(category => (
                <Option key={category.id} value={category.id}>
                  {category.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="备注"
            name="remark"
          >
            <Input.TextArea placeholder="请输入备注" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default BillsPage;
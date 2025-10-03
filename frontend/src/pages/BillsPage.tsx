import React, { useEffect, useState, useRef, useCallback } from 'react';
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
import { ClassificationRuleService } from '../api/services';
import type { SourceTypeOption } from '../types';
import { useFamilyStore } from '../stores/family';

const { Text } = Typography;
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
    batchUpdateBills,
  } = useBillsStore();
  // 新增：家庭成员 store
  const { members, currentFamily, fetchFamilyMembers, loading: familyLoading, fetchFamilies } = useFamilyStore();
  // 页面初始化：如无当前家庭，主动加载家庭列表
  useEffect(() => {
    if (!currentFamily) {
      fetchFamilies();
    }
  }, [currentFamily, fetchFamilies]);
  // 当当前家庭变化时，加载成员列表
  useEffect(() => {
    if (currentFamily?.id) {
      fetchFamilyMembers(currentFamily.id);
    }
  }, [currentFamily?.id, fetchFamilyMembers]);

  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingBill, setEditingBill] = useState<Bill | null>(null);
  const [form] = Form.useForm();
  // 来源选项状态
  const [sourceTypeOptions, setSourceTypeOptions] = useState<SourceTypeOption[]>([]);
  const [loadingSourceTypes, setLoadingSourceTypes] = useState<boolean>(false);
  // 新增：批量选择与批量更新弹窗
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [isBatchModalVisible, setIsBatchModalVisible] = useState(false);
  // 账单表格滚动容器，用于 Table sticky 绑定
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [batchForm] = Form.useForm();

  // 搜索区域显示/隐藏状态
  const [isSearchVisible, setIsSearchVisible] = useState(true);
  const [lastScrollTop, setLastScrollTop] = useState(0);
  const scrollThreshold = 50; // 滚动阈值，超过此距离才触发显示/隐藏
  const [searchAreaHeight, setSearchAreaHeight] = useState(120); // 动态搜索区域高度
  const searchAreaRef = useRef<HTMLDivElement | null>(null);

  // 滚动监听逻辑 - 添加防抖优化
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;
    
    const currentScrollTop = scrollContainerRef.current.scrollTop;
    const scrollDiff = currentScrollTop - lastScrollTop;
    
    // 使用 requestAnimationFrame 优化性能
    requestAnimationFrame(() => {
      // 向下滚动且超过阈值时隐藏搜索区域
      if (scrollDiff > scrollThreshold && currentScrollTop > scrollThreshold) {
        if (isSearchVisible) {
          setIsSearchVisible(false);
        }
      }
      // 向上滚动且超过阈值时显示搜索区域
      else if (scrollDiff < -scrollThreshold || currentScrollTop <= scrollThreshold) {
        if (!isSearchVisible) {
          setIsSearchVisible(true);
        }
      }
    });
    
    setLastScrollTop(currentScrollTop);
  }, [lastScrollTop, scrollThreshold, isSearchVisible]);

  // 添加滚动监听器
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll, { passive: true });
      return () => {
        scrollContainer.removeEventListener('scroll', handleScroll);
      };
    }
  }, [handleScroll]);

  // 动态检测搜索区域高度
  useEffect(() => {
    const updateSearchAreaHeight = () => {
      if (searchAreaRef.current) {
        const height = searchAreaRef.current.offsetHeight;
        setSearchAreaHeight(height);
      }
    };

    // 初始检测
    updateSearchAreaHeight();

    // 监听窗口大小变化
    const resizeObserver = new ResizeObserver(updateSearchAreaHeight);
    if (searchAreaRef.current) {
      resizeObserver.observe(searchAreaRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // 当编辑弹窗打开且存在当前账单时，同步表单字段，确保分类等字段正常显示
  useEffect(() => {
    if (isModalVisible && editingBill) {
      const rawCategoryId = editingBill.category_id ?? editingBill.category?.id;
      const categoryIdNormalized = typeof rawCategoryId === 'string'
        ? Number(rawCategoryId)
        : rawCategoryId;

      form.setFieldsValue({
        amount: editingBill.amount,
        transaction_type: editingBill.transaction_type,
        transaction_desc: editingBill.transaction_desc,
        category_id: Number.isFinite(categoryIdNormalized as number) ? categoryIdNormalized : undefined,
        remark: editingBill.remark ?? editingBill.raw_data?.remark ?? '',
      });
    } else if (isModalVisible && !editingBill) {
      // 新增模式：确保完全重置表单并设置默认值
      form.resetFields();
      // 使用 setTimeout 确保重置操作完成后再设置默认值
      setTimeout(() => {
        form.setFieldsValue({
          transaction_time: dayjs(),
          source_type: 'manual',
        });
      }, 0);
    }
  }, [isModalVisible, editingBill, form]);
  // 获取来源类型中文名（优先从动态选项，其次回退到内置映射，最后原值）
  const getSourceTypeLabel = (value: string) => {
    const found = sourceTypeOptions.find(opt => opt.value === value)?.label;
    if (found) return found;
    const fallbackMap: Record<string, string> = {
      alipay: '支付宝',
      jd: '京东',
      cmb: '招商银行',
      wechat: '微信支付',
      meituan: '美团',
      manual: '手动录入',
    };
    return fallbackMap[value] || value;
  };

  // 加载来源选项（动态）
  const fetchSourceTypes = async () => {
    setLoadingSourceTypes(true);
    const fallback: SourceTypeOption[] = [
      { value: 'alipay', label: '支付宝' },
      { value: 'jd', label: '京东' },
      { value: 'cmb', label: '招商银行' },
      { value: 'wechat', label: '微信支付' },
      { value: 'meituan', label: '美团' },
      { value: 'manual', label: '手动录入' },
    ];
    try {
      const res = await ClassificationRuleService.getSourceTypeOptions();
      if (res.success) {
        // 过滤掉不适合筛选的“全部/all”项
        const opts = (res.data?.source_types || []).filter(opt => opt.value !== 'all');
        setSourceTypeOptions(opts);
      } else {
        message.error(res.message || '获取来源选项失败');
        setSourceTypeOptions(fallback);
      }
    } catch (err: any) {
      message.error(err?.message || '获取来源选项失败');
      setSourceTypeOptions(fallback);
    } finally {
      setLoadingSourceTypes(false);
    }
  };

  useEffect(() => {
    fetchBills();
    fetchCategories();
    fetchSourceTypes();
  }, [fetchBills, fetchCategories]);

  // 新增：当全局查询参数包含 start_date/end_date 时，自动将日期范围控件同步到该值
  useEffect(() => {
    const start = queryParams.start_date;
    const end = queryParams.end_date;
    if (start && end) {
      setDateRange([dayjs(start), dayjs(end)]);
    } else {
      // 若清空了全局日期条件，同步清空控件
      setDateRange(null);
    }
  }, [queryParams.start_date, queryParams.end_date]);

  // 处理筛选
  const handleFilter = (key: keyof BillListQueryParams, value: any) => {
    setQueryParams({
      [key]: value,
      page: 1,
      size: 100,
    });
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
          // DatePicker 返回 Dayjs；转换为 ISO 字符串以兼容后端 datetime
          transaction_time: values.transaction_time
            ? values.transaction_time.toDate().toISOString()
            : new Date().toISOString(),
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
      size: 100,
      sort_by: 'transaction_date',
      sort_order: 'desc',
      search: undefined,
      transaction_type: undefined,
      source_type: undefined,
      category_id: undefined,
      start_date: undefined,
      end_date: undefined,
      min_amount: undefined,
      max_amount: undefined,
      // 新增：重置成员筛选
      user_id: undefined,
    });
  };

  // 查询按钮 - 触发搜索
  const handleQuery = () => {
    // 金额区间校验（若两者都填）
    const minAmt = queryParams.min_amount;
    const maxAmt = queryParams.max_amount;
    if (
      typeof minAmt === 'number' && typeof maxAmt === 'number' &&
      !Number.isNaN(minAmt) && !Number.isNaN(maxAmt) &&
      minAmt > maxAmt
    ) {
      message.error('最小金额不能大于最大金额');
      return;
    }

    const nextParams = { ...queryParams, page: 1, size: 100 } as BillListQueryParams;
    setQueryParams(nextParams);
    fetchBills(nextParams);
  };

  // 表格列定义
  const columns: ColumnsType<Bill> = [
    {
      title: '交易时间',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 200,
      render: (date: string) => (
        <span style={{ whiteSpace: 'nowrap' }}>
          {dayjs(date).format('YYYY-MM-DD HH:mm:ss')}
        </span>
      ),
      sorter: (a: Bill, b: Bill) => {
        const dateA = dayjs(a.transaction_date);
        const dateB = dayjs(b.transaction_date);
        return dateA.valueOf() - dateB.valueOf();
      },
    },
    {
      title: '交易描述',
      dataIndex: 'transaction_desc',
      key: 'transaction_desc',
      ellipsis: true,
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (remark: string | undefined) => (
        <span style={{ color: '#666' }}>{remark || ''}</span>
      ),
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
      sorter: (a: Bill, b: Bill) => a.amount - b.amount,
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
      render: (source: string) => getSourceTypeLabel(source),
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

  return (<>
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%', 
      position: 'relative',
    }}>
      <div style={{ display: 'none' }} />

      {/* 筛选区域 */}
      <Card 
        ref={searchAreaRef}
        style={{ 
          marginBottom: isSearchVisible ? 8 : 0,
          transform: isSearchVisible ? 'translateY(0)' : 'translateY(-100%)',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10,
          opacity: isSearchVisible ? 1 : 0,
        }} 
        bodyStyle={{ padding: 12 }}
      >
        <Space wrap align="center" size={8}>
          {/* 家庭成员筛选：调整为首位 */}
          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>家庭成员：</Text>
            <Select
              placeholder="请选择"
              style={{ width: 240 }}
              mode="multiple"
              allowClear
              maxTagCount={2}
              size="small"
              loading={familyLoading}
              value={Array.isArray(queryParams.user_id)
                ? queryParams.user_id
                : (typeof queryParams.user_id === 'number' ? [queryParams.user_id] : undefined)}
              onChange={(values) => handleFilter('user_id', values)}
              notFoundContent={familyLoading ? '加载中...' : '暂无成员'}
            >
              {members.map(m => (
                <Option key={m.user_id} value={m.user_id}>
                  {m.user?.full_name || m.user?.username || `用户#${m.user_id}`}
                </Option>
              ))}
            </Select>
          </Space>
          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>交易描述：</Text>
            <Input
              placeholder="请输入交易描述"
              value={searchText}
              size="small"
              onChange={(e) => {
                setSearchText(e.target.value);
                setQueryParams({
                  search: e.target.value,
                  page: 1,
                  size: 100,
                });
              }}
              style={{ width: 200 }}
            />
          </Space>

          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>交易类型：</Text>
            <Select
              placeholder="请选择"
              style={{ width: 240 }}
              mode="multiple"
              allowClear
              maxTagCount={2}
              size="small"
              onChange={(values) => handleFilter('transaction_type', values)}
              value={Array.isArray(queryParams.transaction_type)
                ? queryParams.transaction_type
                : (typeof queryParams.transaction_type === 'string' ? [queryParams.transaction_type] : undefined)}
            >
              <Option value="income">收入</Option>
              <Option value="expense">支出</Option>
              <Option value="transfer">不计收支</Option>
            </Select>
          </Space>

          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>来源：</Text>
            <Select
              placeholder="请选择"
              style={{ width: 240 }}
              mode="multiple"
              allowClear
              maxTagCount={2}
              loading={loadingSourceTypes}
              size="small"
              onChange={(values) => handleFilter('source_type', values)}
              value={Array.isArray(queryParams.source_type)
                ? queryParams.source_type
                : (typeof queryParams.source_type === 'string' ? [queryParams.source_type] : undefined)}
              notFoundContent={loadingSourceTypes ? '加载中...' : '暂无数据'}
            >
              {sourceTypeOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Space>

          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>分类：</Text>
            <Select
              placeholder="请选择分类"
              style={{ width: 240 }}
              mode="multiple"
              allowClear
              maxTagCount={2}
              size="small"
              onChange={(values) => handleFilter('category_id', values)}
              value={Array.isArray(queryParams.category_id)
                ? queryParams.category_id
                : (typeof queryParams.category_id === 'number' ? [queryParams.category_id] : undefined)}
            >
              {categories.map(category => (
                <Option key={category.id} value={category.id}>
                  {category.name}
                </Option>
              ))}
            </Select>
          </Space>

          {/* 家庭成员筛选已调整至首位 */}

          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>日期范围：</Text>
            <RangePicker
              placeholder={["开始日期", "结束日期"]}
              value={dateRange}
              size="small"
              onChange={(dates) => {
                setDateRange(dates);
                if (dates && dates[0] && dates[1]) {
                  setQueryParams({
                    start_date: dates[0].format('YYYY-MM-DD'),
                    end_date: dates[1].format('YYYY-MM-DD'),
                    page: 1,
                    size: 100,
                  });
                } else {
                  setQueryParams({
                    start_date: undefined,
                    end_date: undefined,
                    page: 1,
                    size: 100,
                  });
                }
              }}
            />
          </Space>

          {/* 新增：金额区间 */}
          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>最小金额：</Text>
            <InputNumber
              placeholder="最小金额"
              style={{ width: 120 }}
              min={0}
              precision={2}
              size="small"
              value={queryParams.min_amount}
              onChange={(val) => handleFilter('min_amount', typeof val === 'number' ? val : undefined)}
            />
          </Space>
          <Space align="center">
            <Text style={{ display: 'inline-block', width: 80, textAlign: 'right' }}>最大金额：</Text>
            <InputNumber
              placeholder="最大金额"
              style={{ width: 120 }}
              min={0}
              precision={2}
              size="small"
              value={queryParams.max_amount}
              onChange={(val) => handleFilter('max_amount', typeof val === 'number' ? val : undefined)}
            />
          </Space>
        </Space>
        <div style={{ marginTop: 8, display: 'flex', justifyContent: 'center' }}>
          <Space size="middle">
            <Button type="primary" size="small" onClick={handleQuery}>
              查询
            </Button>
            <Button size="small" onClick={handleReset}>
              重置
            </Button>
            <Button
              icon={<PlusOutlined />}
              size="small"
              onClick={() => {
                // 新增账单：确保完全清空上一次编辑残留
                setEditingBill(null);
                // 先重置表单，确保清空所有字段
                form.resetFields();
                // 打开弹框
                setIsModalVisible(true);
                // 使用 setTimeout 确保表单重置完成后再设置默认值
                setTimeout(() => {
                  form.setFieldsValue({ 
                    transaction_time: dayjs(), 
                    source_type: 'manual' 
                  });
                }, 0);
              }}
            >
              新增账单
            </Button>
            {/* 新增：批量更新按钮 */}
            <Button
              size="small"
              disabled={selectedRowKeys.length === 0}
              onClick={() => setIsBatchModalVisible(true)}
            >
              批量更新
            </Button>
          </Space>
        </div>
      </Card>

      {/* 账单表格 */}
      <div 
        style={{ 
          flex: 1, 
          overflow: 'auto', 
          minHeight: 0,
          paddingTop: isSearchVisible ? `${searchAreaHeight}px` : '0px',
        }} 
        ref={scrollContainerRef}
      >
        <Table
          columns={columns}
          dataSource={bills}
          rowKey="id"
          loading={isLoading}
          size="small"
          sticky={{ getContainer: () => scrollContainerRef?.current || document.body }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
          pagination={false}
          onChange={(_paginationInfo, _filters, _sorter) => {
            // 移除排序逻辑，仅保留客户端排序
          }}
          scroll={{ x: 800 }}
        />
      </div>

      {/* 固定在底部的翻页组件 */}
      <div style={{ 
        position: 'sticky', 
        bottom: 0, 
        backgroundColor: '#fff', 
        padding: '12px 0', 
        borderTop: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'center',
        zIndex: 10,
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '16px',
          fontSize: '14px'
        }}>
          <span>共 {pagination.total} 条记录</span>
          <Button 
            size="small" 
            disabled={pagination.page <= 1}
            onClick={() => handlePageChange(pagination.page - 1, pagination.size)}
          >
            上一页
          </Button>
          <span>
            第 {pagination.page} 页 / 共 {Math.ceil(pagination.total / pagination.size)} 页
          </span>
          <Button 
            size="small" 
            disabled={pagination.page >= Math.ceil(pagination.total / pagination.size)}
            onClick={() => handlePageChange(pagination.page + 1, pagination.size)}
          >
            下一页
          </Button>
          <Select
            size="small"
            value={pagination.size}
            onChange={(size) => handlePageChange(1, size)}
            style={{ width: 80 }}
          >
            <Option value={10}>10条</Option>
            <Option value={20}>20条</Option>
            <Option value={50}>50条</Option>
            <Option value={100}>100条</Option>
          </Select>
        </div>
      </div>

      {/* 编辑/新增模态框 */}
      <Modal
        title={editingBill ? '编辑账单' : '新增账单'}
        open={isModalVisible}
        destroyOnClose
        afterClose={() => {
          // 关闭后确保下一次打开为干净状态
          form.resetFields();
          setEditingBill(null);
        }}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingBill(null);
          form.resetFields();
        }}
        footer={[
          <Button key="cancel" onClick={() => {
            setIsModalVisible(false);
            setEditingBill(null);
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
          key={editingBill ? String(editingBill.id) : 'create'}
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          preserve={false}
          initialValues={editingBill ? {
            amount: editingBill.amount,
            transaction_type: editingBill.transaction_type,
            transaction_desc: editingBill.transaction_desc,
            category_id: (() => {
              const raw = editingBill.category_id ?? editingBill.category?.id;
              const n = typeof raw === 'string' ? Number(raw) : raw;
              return Number.isFinite(n as number) ? n : undefined;
            })(),
            remark: editingBill.remark ?? editingBill.raw_data?.remark ?? '',
          } : {
            // AntD v5 使用 Dayjs：默认值改为 dayjs()
            transaction_time: dayjs(),
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
      {/* 批量更新模态框 */}
      <Modal
        title={'批量更新账单'}
        open={isBatchModalVisible}
        onCancel={() => {
          setIsBatchModalVisible(false);
          batchForm.resetFields();
        }}
        footer={[
          <Button key="cancel" onClick={() => {
            setIsBatchModalVisible(false);
            batchForm.resetFields();
          }}>
            取消
          </Button>,
          <Button key="submit" type="primary" onClick={async () => {
            try {
              const values = await batchForm.validateFields();
              await batchUpdateBills(selectedRowKeys, values);
              message.success('批量更新成功');
              setIsBatchModalVisible(false);
              batchForm.resetFields();
              setSelectedRowKeys([]);
            } catch (err: any) {
              if (err?.errorFields) return;
              message.error(err?.message || '批量更新失败');
            }
          }} loading={isLoading}>
            更新
          </Button>,
        ]}
        width={520}
      >
        <Form form={batchForm} layout="vertical">
          <Form.Item label="交易类型" name="transaction_type">
            <Select placeholder="请选择交易类型" allowClear>
              <Option value="income">收入</Option>
              <Option value="expense">支出</Option>
              <Option value="transfer">不计收支</Option>
            </Select>
          </Form.Item>
          <Form.Item label="分类" name="category_id">
            <Select placeholder="请选择分类" allowClear>
              {categories.map(category => (
                <Option key={category.id} value={category.id}>
                  {category.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="备注" name="remark">
            <Input.TextArea placeholder="请输入备注" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
    </>
  );
};

export default BillsPage;
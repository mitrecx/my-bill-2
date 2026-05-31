import React, { useState, useEffect } from 'react';
import {
  Alert,
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  message,
  Popconfirm,
  Row,
  Col,
  Typography,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PoweroffOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { ClassificationRuleService, BillService } from '../api/services';
import type {
  ClassificationRule,
  SourceTypeOption,
  TransactionTypeOption,
  BillCategory,
} from '../types';
import type { ColumnsType } from 'antd/es/table';
import TransactionTypeTag from '../components/TransactionTypeTag';

const { Text } = Typography;
const { Option } = Select;

interface RuleFormData {
  scope: 'personal' | 'family';
  rule_text: string;
  source_type: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual' | 'all';
  target_category: string;
  transaction_type: 'expense' | 'income' | 'transfer';
  priority: number;
  is_active: boolean;
}

const ClassificationRulesPage: React.FC = () => {
  const [rules, setRules] = useState<ClassificationRule[]>([]);
  const [sourceTypeOptions, setSourceTypeOptions] = useState<SourceTypeOption[]>([]);
  const [transactionTypeOptions, setTransactionTypeOptions] = useState<TransactionTypeOption[]>([]);
  const [categories, setCategories] = useState<BillCategory[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 分页状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 100,
    total: 0,
  });
  
  // 筛选状态
  const [filters, setFilters] = useState({
    scope: '',
    source_type: '',
    target_category: '',
    transaction_type: '',
    is_active: undefined as boolean | undefined,
    search: '',
  });
  
  // 搜索输入状态
  const [searchInput, setSearchInput] = useState('');
  
  // 对话框状态
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ClassificationRule | null>(null);
  const [form] = Form.useForm<RuleFormData>();
  const selectedTransactionType = Form.useWatch('transaction_type', form);

  const filteredCategories = categories.filter((category) => {
    if (!selectedTransactionType || selectedTransactionType === 'transfer') {
      return true;
    }
    return category.category_type === selectedTransactionType;
  });

  // 获取来源类型选项
  const fetchSourceTypeOptions = async () => {
    try {
      const response = await ClassificationRuleService.getSourceTypeOptions();
      if (response.success) {
        setSourceTypeOptions(response.data.source_types);
      }
    } catch (error) {
      console.error('获取来源类型选项失败:', error);
    }
  };

  // 获取交易类型选项
  const fetchTransactionTypeOptions = async () => {
    try {
      const response = await ClassificationRuleService.getTransactionTypeOptions();
      if (response.success) {
        setTransactionTypeOptions(response.data.transaction_types);
      }
    } catch (error) {
      console.error('获取交易类型选项失败:', error);
    }
  };

  // 获取账单分类
  const fetchCategories = async () => {
    try {
      const response = await BillService.getCategories();
      if (response.success) {
        setCategories(response.data);
      }
    } catch (error) {
      console.error('获取账单分类失败:', error);
    }
  };

  // 获取分类规则列表
  const fetchRules = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
      };
      
      if (filters.scope) params.scope = filters.scope;
      if (filters.source_type) params.source_type = filters.source_type;
      if (filters.target_category) params.target_category = filters.target_category;
      if (filters.transaction_type) params.transaction_type = filters.transaction_type;
      if (filters.is_active !== undefined) params.is_active = filters.is_active;
      if (filters.search) params.search = filters.search;

      const response = await ClassificationRuleService.getRules(params);
      if (response.success) {
        setRules(response.data.rules);
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total,
        });
      } else {
        message.error(response.message || '获取分类规则失败');
      }
    } catch (error: any) {
      message.error(error.message || '获取分类规则失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchSourceTypeOptions();
    fetchTransactionTypeOptions();
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchRules(pagination.current, pagination.pageSize);
  }, [filters]);

  // 打开创建对话框
  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      scope: 'personal',
      source_type: 'all',
      transaction_type: 'expense',
      priority: 1,
      is_active: true,
    });
    setModalVisible(true);
  };

  // 打开编辑对话框
  const handleEdit = (rule: ClassificationRule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      scope: rule.scope,
      rule_text: rule.rule_text,
      source_type: rule.source_type,
      target_category: rule.target_category,
      transaction_type: rule.transaction_type,
      priority: rule.priority,
      is_active: rule.is_active,
    });
    setModalVisible(true);
  };

  // 保存规则
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRule) {
        // 更新规则
        const response = await ClassificationRuleService.updateRule(editingRule.id, values);
        if (response.success) {
          message.success('规则更新成功');
          setModalVisible(false);
          fetchRules(pagination.current, pagination.pageSize);
        } else {
          message.error(response.message || '更新规则失败');
        }
      } else {
        // 创建规则
        const response = await ClassificationRuleService.createRule(values);
        if (response.success) {
          message.success('规则创建成功');
          setModalVisible(false);
          fetchRules(pagination.current, pagination.pageSize);
        } else {
          message.error(response.message || '创建规则失败');
        }
      }
    } catch (error: any) {
      message.error(error.message || '保存规则失败');
    }
  };

  // 删除规则
  const handleDelete = async (id: number) => {
    try {
      const response = await ClassificationRuleService.deleteRule(id);
      if (response.success) {
        message.success('规则删除成功');
        fetchRules(pagination.current, pagination.pageSize);
      } else {
        message.error(response.message || '删除规则失败');
      }
    } catch (error: any) {
      message.error(error.message || '删除规则失败');
    }
  };

  // 切换规则状态
  const handleToggleStatus = async (id: number) => {
    try {
      const response = await ClassificationRuleService.toggleRuleStatus(id);
      if (response.success) {
        message.success('规则状态更新成功');
        fetchRules(pagination.current, pagination.pageSize);
      } else {
        message.error(response.message || '更新规则状态失败');
      }
    } catch (error: any) {
      message.error(error.message || '更新规则状态失败');
    }
  };

  // 搜索规则
  const handleSearch = () => {
    setFilters({ ...filters, search: searchInput });
    setPagination({ ...pagination, current: 1 });
  };

  // 重置筛选
  const handleReset = () => {
    setSearchInput('');
    setFilters({ scope: '', source_type: '', target_category: '', transaction_type: '', is_active: undefined, search: '' });
    setPagination({ ...pagination, current: 1 });
  };

  // 获取来源类型标签
  const getSourceTypeLabel = (sourceType: string) => {
    const option = sourceTypeOptions.find(opt => opt.value === sourceType);
    return option ? option.label : sourceType;
  };

  // 获取分类名称
  const getCategoryName = (categoryName: string) => {
    const category = categories.find(cat => cat.name === categoryName);
    return category ? category.name : categoryName;
  };

  // 表格列定义
  const columns: ColumnsType<ClassificationRule> = [
    {
      title: '规则文本',
      dataIndex: 'rule_text',
      key: 'rule_text',
      width: 200,
      ellipsis: {
        showTitle: false,
      },
      render: (text: string) => (
        <Tooltip placement="topLeft" title={text}>
          {text}
        </Tooltip>
      ),
    },
    {
      title: '作用域',
      dataIndex: 'scope',
      key: 'scope',
      width: 80,
      render: (scope: string) => (
        <Tag color={scope === 'family' ? 'purple' : 'cyan'}>
          {scope === 'family' ? '家庭' : '个人'}
        </Tag>
      ),
    },
    {
      title: '来源类型',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 120,
      render: (sourceType: string) => (
        <Tag color="blue">{getSourceTypeLabel(sourceType)}</Tag>
      ),
    },
    {
      title: '收支类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 90,
      render: (transactionType: string) => (
        <TransactionTypeTag type={transactionType} />
      ),
    },
    {
      title: '目标分类',
      dataIndex: 'target_category',
      key: 'target_category',
      width: 150,
      render: (category: string) => getCategoryName(category),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      sorter: (a, b) => a.priority - b.priority,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_active ? '禁用' : '启用'}>
            <Button
              type="text"
              icon={<PoweroffOutlined />}
              onClick={() => handleToggleStatus(record.id)}
              style={{ color: record.is_active ? '#ff4d4f' : '#52c41a' }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个分类规则吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Alert
        type="info"
        showIcon
        message="分类规则支持个人级与家庭级"
        description="个人级规则仅对创建者生效；家庭级规则对全部家庭成员生效，成员均可管理。导入账单开启「AI 自动分类」时，会合并使用你的个人规则与家庭规则，写入提示词供 AI 优先参考（非程序硬匹配）。"
        style={{ marginBottom: 16 }}
      />

      {/* 筛选和操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle" style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={6}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              <Text style={{ flex: '0 0 80px', textAlign: 'right' }}>规则文本：</Text>
              <Input
                placeholder="请输入规则文本"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onPressEnter={handleSearch}
                allowClear
                style={{ flex: 1, minWidth: 0 }}
              />
            </div>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              <Text style={{ flex: '0 0 80px', textAlign: 'right' }}>作用域：</Text>
              <Select
                placeholder="请选择"
                value={filters.scope || undefined}
                onChange={(value) => setFilters({ ...filters, scope: value || '' })}
                allowClear
                style={{ flex: 1, minWidth: 0 }}
              >
                <Option value="personal">个人</Option>
                <Option value="family">家庭</Option>
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              <Text style={{ flex: '0 0 80px', textAlign: 'right' }}>来源类型：</Text>
              <Select
                placeholder="请选择"
                value={filters.source_type || undefined}
                onChange={(value) => setFilters({ ...filters, source_type: value || '' })}
                allowClear
                style={{ flex: 1, minWidth: 0 }}
              >
                {sourceTypeOptions.map((option) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              <Text style={{ flex: '0 0 80px', textAlign: 'right' }}>目标分类：</Text>
              <Select
                placeholder="请选择"
                value={filters.target_category || undefined}
                onChange={(value) => setFilters({ ...filters, target_category: value || '' })}
                allowClear
                style={{ flex: 1, minWidth: 0 }}
              >
                {categories.map((category) => (
                  <Option key={category.id} value={category.name}>
                    {category.name}
                  </Option>
                ))}
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              <Text style={{ flex: '0 0 80px', textAlign: 'right' }}>收支类型：</Text>
              <Select
                placeholder="请选择"
                value={filters.transaction_type || undefined}
                onChange={(value) => setFilters({ ...filters, transaction_type: value || '' })}
                allowClear
                style={{ flex: 1, minWidth: 0 }}
              >
                {transactionTypeOptions.map((option) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              <Text style={{ flex: '0 0 80px', textAlign: 'right' }}>状态：</Text>
              <Select
                placeholder="请选择"
                value={filters.is_active}
                onChange={(value) => setFilters({ ...filters, is_active: value })}
                allowClear
                style={{ flex: 1, minWidth: 0 }}
              >
                <Option value={true}>启用</Option>
                <Option value={false}>禁用</Option>
              </Select>
            </div>
          </Col>

        </Row>

        {/* 操作按钮单独一行：查询/重置/新建 居中 */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <Space size="middle">
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>
              查询
            </Button>
            <Button onClick={handleReset}>重置</Button>
            <Button icon={<PlusOutlined />} onClick={handleCreate}>新建规则</Button>
          </Space>
        </div>
      </Card>

      {/* 规则列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={rules}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPagination({ ...pagination, current: page, pageSize: pageSize || 10 });
              fetchRules(page, pageSize || 10);
            },
          }}
        />
      </Card>

      {/* 创建/编辑对话框 */}
      <Modal
        title={editingRule ? '编辑分类规则' : '新建分类规则'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            scope: 'personal',
            source_type: 'all',
            transaction_type: 'expense',
            priority: 1,
            is_active: true,
          }}
        >
          <Form.Item
            label="作用域"
            name="scope"
            rules={[{ required: true, message: '请选择作用域' }]}
            extra="个人级仅对自己生效；家庭级对全部家庭成员生效（须已加入家庭）"
          >
            <Select placeholder="请选择作用域">
              <Option value="personal">个人</Option>
              <Option value="family">家庭</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="规则文本"
            name="rule_text"
            rules={[{ required: true, message: '请输入规则文本' }]}
            extra="供 AI 参考的自然语言线索（如商户名、关键词），非正则表达式"
          >
            <Input placeholder="请输入规则文本" />
          </Form.Item>
          
          <Form.Item
            label="来源类型"
            name="source_type"
            rules={[{ required: true, message: '请选择来源类型' }]}
          >
            <Select placeholder="请选择来源类型">
              {sourceTypeOptions.map((option) => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="收支类型"
            name="transaction_type"
            rules={[{ required: true, message: '请选择收支类型' }]}
          >
            <Select
              placeholder="请选择收支类型"
              onChange={() => form.setFieldValue('target_category', undefined)}
            >
              {transactionTypeOptions.map((option) => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            label="目标分类"
            name="target_category"
            rules={[{ required: true, message: '请选择目标分类' }]}
          >
            <Select placeholder="请选择目标分类">
              {filteredCategories.map((category) => (
                <Option key={category.id} value={category.name}>
                  {category.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            label="优先级"
            name="priority"
            rules={[{ required: true, message: '请输入优先级' }]}
            extra="数值越大优先级越高"
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            label="启用规则"
            name="is_active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ClassificationRulesPage;
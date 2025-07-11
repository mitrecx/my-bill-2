import React, { useEffect, useState } from 'react';
import {
  Typography,
  Card,
  Row,
  Col,
  DatePicker,
  Select,
  Space,
  Statistic,
  Table,
  Spin,
  Alert,
} from 'antd';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  // BarChart,
  // Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useBillsStore } from '../stores/bills';
// import { useAuthStore } from '../stores/auth';
import { FamilyService } from '../api/services';
import type { CategoryStats, Family } from '../types';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// 定义颜色主题
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658'];

interface TrendData {
  date: string;
  income: number;
  expense: number;
  net: number;
}

const StatsPage: React.FC = () => {
  // const { user } = useAuthStore();
  const { stats, categoryStats, fetchStats, fetchCategoryStats } = useBillsStore();
  
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamily, setSelectedFamily] = useState<number | undefined>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null]>([
    dayjs().subtract(3, 'month'),
    dayjs(),
  ]);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFamilies();
  }, []);

  useEffect(() => {
    if (selectedFamily && dateRange[0] && dateRange[1]) {
      loadStatsData();
    }
  }, [selectedFamily, dateRange]);

  const loadFamilies = async () => {
    try {
      const familiesData = await FamilyService.getFamilies();
      setFamilies(familiesData);
      if (familiesData.length > 0) {
        setSelectedFamily(familiesData[0].id);
      }
    } catch (error) {
      setError('加载家庭列表失败');
    }
  };

  const loadStatsData = async () => {
    if (!selectedFamily || !dateRange[0] || !dateRange[1]) return;

    try {
      setIsLoading(true);
      setError(null);

      const params = {
        family_id: selectedFamily,
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      };

      // 加载统计数据
      await fetchStats(params);
      await fetchCategoryStats(params);

      // 加载趋势数据（模拟月度数据）
      await loadTrendData(params);
    } catch (error: any) {
      setError(error.message || '加载统计数据失败');
    } finally {
      setIsLoading(false);
    }
  };

  const loadTrendData = async (params: { family_id: number; start_date: string; end_date: string }) => {
    // 这里应该调用API获取趋势数据，暂时用模拟数据
    const months = [];
    const start = dayjs(params.start_date);
    const end = dayjs(params.end_date);
    
    let current = start.startOf('month');
    while (current.isBefore(end) || current.isSame(end, 'month')) {
      months.push({
        date: current.format('YYYY-MM'),
        income: Math.random() * 5000 + 1000,
        expense: Math.random() * 8000 + 2000,
        net: 0,
      });
      current = current.add(1, 'month');
    }

    // 计算净收益
    const trendsWithNet = months.map(item => ({
      ...item,
      net: item.income - item.expense,
    }));

    setTrendData(trendsWithNet);
  };

  // 分类统计表格列定义
  const categoryColumns: ColumnsType<CategoryStats> = [
    {
      title: '分类',
      dataIndex: 'category_name',
      key: 'category_name',
    },
    {
      title: '金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount: number) => `¥${amount.toFixed(2)}`,
      sorter: (a, b) => a.total_amount - b.total_amount,
    },
    {
      title: '笔数',
      dataIndex: 'transaction_count',
      key: 'transaction_count',
      sorter: (a, b) => a.transaction_count - b.transaction_count,
    },
    {
      title: '占比',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (percentage: number) => `${percentage.toFixed(1)}%`,
      sorter: (a, b) => a.percentage - b.percentage,
    },
  ];

  // 饼图数据处理
  const pieData = categoryStats.map((item, index) => ({
    name: item.category_name,
    value: item.total_amount,
    color: COLORS[index % COLORS.length],
  }));

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="加载统计数据中..." />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>统计分析</Title>

      {/* 筛选条件 */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="large">
          <div>
            <Text>家庭：</Text>
            <Select
              value={selectedFamily}
              onChange={setSelectedFamily}
              style={{ width: 200, marginLeft: 8 }}
              placeholder="选择家庭"
            >
              {families.map(family => (
                <Option key={family.id} value={family.id}>
                  {family.family_name}
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <Text>时间范围：</Text>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null])}
              style={{ marginLeft: 8 }}
              placeholder={['开始日期', '结束日期']}
            />
          </div>
        </Space>
      </Card>

      {error && (
        <Alert
          message="统计数据加载失败"
          description={error}
          type="error"
          style={{ marginBottom: 24 }}
          showIcon
        />
      )}

      {/* 概览统计 */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="总收入"
                value={stats.total_income}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
                suffix="元"
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="总支出"
                value={stats.total_expense}
                precision={2}
                valueStyle={{ color: '#cf1322' }}
                suffix="元"
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="净收益"
                value={stats.net_amount}
                precision={2}
                valueStyle={{ color: stats.net_amount >= 0 ? '#3f8600' : '#cf1322' }}
                suffix="元"
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="交易笔数"
                value={stats.transaction_count}
                suffix="笔"
              />
            </Card>
          </Col>
        </Row>
      )}

      <Row gutter={[16, 16]}>
        {/* 收支趋势图 */}
        <Col xs={24} lg={16}>
          <Card title="收支趋势" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    `¥${value.toFixed(2)}`, 
                    name === 'income' ? '收入' : name === 'expense' ? '支出' : '净收益'
                  ]}
                />
                <Legend 
                  formatter={(value: string) => 
                    value === 'income' ? '收入' : value === 'expense' ? '支出' : '净收益'
                  }
                />
                <Line type="monotone" dataKey="income" stroke="#3f8600" strokeWidth={2} />
                <Line type="monotone" dataKey="expense" stroke="#cf1322" strokeWidth={2} />
                <Line type="monotone" dataKey="net" stroke="#1890ff" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* 支出分类饼图 */}
        <Col xs={24} lg={8}>
          <Card title="支出分类占比" style={{ height: 400 }}>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => `¥${value.toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ 
                height: 300, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#999'
              }}>
                暂无分类数据
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 分类统计表格 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="分类统计详情">
            <Table
              columns={categoryColumns}
              dataSource={categoryStats}
              rowKey="category_id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default StatsPage;
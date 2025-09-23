import React, { useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Alert } from 'antd';
import { 
  DollarOutlined, 
  ShoppingOutlined, 
  RiseOutlined, 
  FileTextOutlined 
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
import YearlyExpenseChart from '../components/YearlyExpenseChart';
import YearlyProfitChart from '../components/YearlyProfitChart';
import MonthlyExpenseTrendChart from '../components/MonthlyExpenseTrendChart';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const { 
    stats, 
    fetchStats, 
    error 
  } = useBillsStore();



  useEffect(() => {
    // 加载统计数据
    fetchStats();
  }, [fetchStats]);



  return (
    <div>

      {error && (
        <Alert
          message="加载数据失败"
          description={error}
          type="error"
          style={{ marginBottom: 24 }}
          showIcon
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总收入"
              value={stats?.total_income || 0}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
              prefix={<RiseOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总支出"
              value={stats?.total_expense || 0}
              precision={2}
              valueStyle={{ color: '#cf1322' }}
              prefix={<ShoppingOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="净收益"
              value={stats?.net_amount || 0}
              precision={2}
              valueStyle={{ 
                color: (stats?.net_amount || 0) >= 0 ? '#3f8600' : '#cf1322' 
              }}
              prefix={<DollarOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="交易笔数"
              value={stats?.transaction_count || 0}
              prefix={<FileTextOutlined />}
              suffix="笔"
            />
          </Card>
        </Col>
      </Row>

      {/* 年度支出图表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <YearlyExpenseChart />
        </Col>
      </Row>

      {/* 年度收益趋势图表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <YearlyProfitChart />
        </Col>
      </Row>

      {/* 新增：月度支出趋势图表，整行展示，位于年度收益趋势下方 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <MonthlyExpenseTrendChart />
        </Col>
      </Row>

    </div>
  );
};

export default DashboardPage;
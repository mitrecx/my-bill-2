import React, { useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Alert, Spin } from 'antd';
import { RiseOutlined, ShoppingOutlined, DollarOutlined, FileTextOutlined } from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
import { useLocation, useNavigate } from 'react-router-dom';
import YearlyExpenseChart from '../components/YearlyExpenseChart';
import YearlyProfitChart from '../components/YearlyProfitChart';
import MonthlyExpenseTrendChart from '../components/MonthlyExpenseTrendChart';
import MonthlyExpenseCategoryChart from '../components/MonthlyExpenseCategoryChart';
import { useAuthStore } from '../stores/auth';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const { 
    stats, 
    fetchStats, 
    error,
    setDashboardScope,
    dashboardScope,
    isLoading,
    fetchAvailableYears,
    setQueryParams,
    resetQueryParams,
  } = useBillsStore();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  useEffect(() => {
    // 根据路由设置 scope
    const isFamily = location.pathname.includes('family-dashboard');
    setDashboardScope(isFamily ? 'family' : 'personal');
  }, [location.pathname, setDashboardScope]);

  useEffect(() => {
    // 加载统计数据（跟随 scope 变化）
    fetchStats({ scope: dashboardScope });
  }, [fetchStats, dashboardScope]);

  useEffect(() => {
    // 获取有账单数据的年份列表
    fetchAvailableYears();
  }, [fetchAvailableYears]);

  // 处理总收入卡片点击
  const handleIncomeClick = () => {
    resetQueryParams();
    setQueryParams({
      transaction_type: ['income'],
      user_id: user?.id, // 始终限定为当前登录用户
      page: 1,
      size: 100,
    });
    navigate('/bills');
  };

  // 处理总支出卡片点击
  const handleExpenseClick = () => {
    resetQueryParams();
    setQueryParams({
      transaction_type: ['expense'],
      user_id: user?.id, // 始终限定为当前登录用户
      page: 1,
      size: 100,
    });
    navigate('/bills');
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          {dashboardScope === 'personal' ? '个人仪表板' : '家庭仪表板'}
        </Title>
      </div>

      {error && (
        <Alert
          message="加载数据失败"
          description={error}
          type="error"
          style={{ marginBottom: 24 }}
          showIcon
        />
      )}

      {/* 加载遮罩层 */}
      <Spin spinning={isLoading} tip="数据加载中...">
        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ cursor: 'pointer' }} onClick={handleIncomeClick}>
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
          <Card style={{ cursor: 'pointer' }} onClick={handleExpenseClick}>
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

      {/* 新增：月度支出分类图表，位于"月度支出趋势"下方 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <MonthlyExpenseCategoryChart />
        </Col>
      </Row>
      </Spin>
    </div>
  );
};

export default DashboardPage;
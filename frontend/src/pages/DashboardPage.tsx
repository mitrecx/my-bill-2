import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, Spin, Alert } from 'antd';
import { 
  DollarOutlined, 
  ShoppingOutlined, 
  RiseOutlined, 
  FileTextOutlined 
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
import { BillService } from '../api/services';
import type { Bill } from '../types';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const { 
    stats, 
    fetchStats, 
    error 
  } = useBillsStore();

  const [recentBills, setRecentBills] = useState<Bill[]>([]);
  const [recentLoading, setRecentLoading] = useState<boolean>(false);
  const [recentError, setRecentError] = useState<string | null>(null);

  useEffect(() => {
    // 加载统计数据
    fetchStats();

    // 加载最近账单（局部状态，不写入全局 store）
    const loadRecentBills = async () => {
      setRecentLoading(true);
      setRecentError(null);
      try {
        const response = await BillService.getBills({ page: 1, size: 5, sort_by: 'transaction_time', sort_order: 'desc' });
        setRecentBills(response.data.items || []);
      } catch (e: any) {
        const msg = e?.friendlyMessage || e?.response?.data?.message || e?.response?.data?.detail || '获取最近账单失败';
        setRecentError(msg);
      } finally {
        setRecentLoading(false);
      }
    };

    loadRecentBills();
  }, [fetchStats]);

  const combinedError = error || recentError;

  return (
    <div>

      {combinedError && (
        <Alert
          message="加载数据失败"
          description={combinedError}
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

      {/* 最近账单 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card 
            title="最近账单" 
            extra={<a href="/bills">查看全部</a>}
          >
            {recentLoading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Spin size="large" tip="加载中..." />
              </div>
            ) : (recentBills.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                暂无账单数据
              </div>
            ) : (
              <div>
                {recentBills.map((bill) => (
                  <div 
                    key={bill.id} 
                    style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px 0',
                      borderBottom: '1px solid #f0f0f0'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 'bold' }}>
                        {bill.transaction_desc}
                      </div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        {bill.transaction_date} · {bill.source_type}
                      </div>
                    </div>
                    <div style={{ 
                      fontWeight: 'bold',
                      color: bill.transaction_type === 'income' ? '#3f8600' : '#cf1322'
                    }}>
                      {bill.transaction_type === 'income' ? '+' : '-'}
                      {bill.amount.toFixed(2)}元
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;
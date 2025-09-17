import React, { useState, useEffect } from 'react';
import { Card, Select, Spin, Alert, Typography, Segmented } from 'antd';
import { Line, Column } from '@ant-design/charts';
import { LineChartOutlined, BarChartOutlined } from '@ant-design/icons';
import { BillService } from '../api/services';

const { Title } = Typography;
const { Option } = Select;

interface MonthlyExpenseItem {
  month: number;
  amount: number;
  month_name: string;
  series?: string; // 新增：用于强制固定系列名称，避免 tooltip 误用 x 轴值
}

interface YearlyExpenseChartData {
  year: number;
  monthly_expenses: MonthlyExpenseItem[];
  total_year_expense: number;
}

type ChartType = 'line' | 'column';

const YearlyExpenseChart: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [chartData, setChartData] = useState<MonthlyExpenseItem[]>([]);
  const [totalExpense, setTotalExpense] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [chartType, setChartType] = useState<ChartType>('line');

  // 生成年份选项（当前年份往前推5年）
  const generateYearOptions = () => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = 0; i < 6; i++) {
      years.push(currentYear - i);
    }
    return years;
  };

  // 加载图表数据
  const loadChartData = async (year: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await BillService.getYearlyExpenseChart(year);
      
      if (response.success && response.data) {
        const data: YearlyExpenseChartData = response.data;
        // 映射并兜底，确保前端渲染与 tooltip 不会出现 null/NaN
        const sanitizeAmount = (raw: any): number => {
          if (raw === null || raw === undefined) return 0;
          const s = typeof raw === 'string' ? raw.trim().toLowerCase() : raw;
          if (s === '' || s === 'null' || s === 'nan' || s === '-') return 0;
          const n = Number(raw);
          return Number.isFinite(n) ? n : 0;
        };
        const mapped: MonthlyExpenseItem[] = (data.monthly_expenses || []).map((it: any) => {
          const month = typeof it?.month === 'number' ? it.month : Number(it?.month) || 0;
          const amount = sanitizeAmount(it?.amount);
          const month_name = (() => {
            const v = it?.month_name;
            if (typeof v === 'string' && v.trim() !== '' && v.trim().toLowerCase() !== 'null') return v;
            return month ? `${month}月` : '';
          })();
          return { month, amount, month_name, series: '支出金额' } as MonthlyExpenseItem; // 加入固定系列名称
        });
        setChartData(mapped);
        const ty = sanitizeAmount(data.total_year_expense as any);
        setTotalExpense(ty);
      } else {
        throw new Error(response.message || '获取数据失败');
      }
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail || e?.message || '获取年度支出数据失败';
      setError(errorMsg);
      setChartData([]);
      setTotalExpense(0);
    } finally {
      setLoading(false);
    }
  };

  // 年份变化处理
  const handleYearChange = (year: number) => {
    setSelectedYear(year);
    loadChartData(year);
  };

  // 组件挂载时加载当前年份数据
  useEffect(() => {
    loadChartData(selectedYear);
  }, []);

  // 基础图表配置
  const baseChartConfig = {
    data: chartData,
    xField: 'month_name',
    yField: 'amount',
    height: 300,
    seriesField: 'series', // 固定系列，确保 tooltip name 来源一致
    legend: false as const, // 单系列不显示图例，避免视觉冗余
    meta: {
      amount: {
        alias: '支出金额',
        formatter: (v: any) => {
          const n = Number(v);
          const val = Number.isFinite(n) ? n : 0;
          return `¥${val.toFixed(2)}`;
        },
      },
    },
    tooltip: {
      customContent: (title: string, items: any[]) => {
        // 保证返回非空 HTML，避免库对 null/空字符串的特殊处理导致显示 "null"
        if (!items || items.length === 0) {
          return '<div class="g2-tooltip"></div>';
        }
        const item = items[0] || {};
        const rawAmount = item?.data?.amount;
        const amountNum = Number(rawAmount);
        const amount = Number.isFinite(amountNum) ? amountNum : 0;
        const safeTitle = (item?.data?.month_name) || (item?.data?.month ? `${item.data.month}月` : (typeof title === 'string' ? title : '')) || '';
        return `
          <div class="g2-tooltip">
            ${safeTitle ? `<div class="g2-tooltip-title">${safeTitle}</div>` : ''}
            <ul class="g2-tooltip-list">
              <li class="g2-tooltip-list-item">
                <span class="g2-tooltip-marker" style="background-color: ${item?.color || '#1890ff'}"></span>
                <span class="g2-tooltip-name">支出金额:</span>
                <span class="g2-tooltip-value">¥${amount.toFixed(2)}</span>
              </li>
            </ul>
          </div>
        `;
      },
      // 关键兜底：即便使用默认模板，也强制改写 items 的 name/value，彻底杜绝 null
      customItems: (originalItems: any[] = []) => {
        return originalItems.map((it: any) => {
          const n = Number(it?.data?.amount);
          const amount = Number.isFinite(n) ? n : 0;
          return {
            ...it,
            name: '支出金额',
            value: `¥${amount.toFixed(2)}`,
          };
        });
      },
      // 兜底：若 customContent 未被生效，则使用 formatter 确保不会出现 null
      fields: ['month_name', 'amount'],
      formatter: (datum: any) => {
        const n = Number(datum?.amount);
        const amount = Number.isFinite(n) ? n : 0;
        return {
          name: '支出金额',
          value: `¥${amount.toFixed(2)}`,
        };
      },
    },
    yAxis: {
      label: {
        formatter: (value: string) => {
          // 安全处理非数字值
          const numValue = parseFloat(value);
          return `¥${isNaN(numValue) ? 0 : numValue.toFixed(0)}`;
        },
      },
    },
    animation: {
      appear: {
        animation: 'wave-in',
        duration: 1000,
      },
    },
  };

  // 折线图配置
  const lineChartConfig = {
    ...baseChartConfig,
    point: {
      size: 5,
      shape: 'diamond' as const,
    },
    label: {
      style: {
        fill: '#aaa',
      },
      formatter: (datum: MonthlyExpenseItem) => {
        const n = Number(datum?.amount);
        const amount = Number.isFinite(n) ? n : 0;
        return amount > 0 ? `¥${Math.round(amount)}` : '';
      },
    },
    color: '#1890ff',
    smooth: true,
  };

  // 直方图配置
  const columnChartConfig = {
    ...baseChartConfig,
    color: '#52c41a',
    columnWidthRatio: 0.6,
    label: {
      position: 'top' as const,
      style: {
        fill: '#666',
        fontSize: 12,
      },
      formatter: (datum: MonthlyExpenseItem) => {
        // 安全处理null/undefined值
        const amount = datum?.amount ?? 0;
        return amount > 0 ? `¥${amount.toFixed(0)}` : '';
      },
    },
  };

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>年度支出趋势</Title>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Segmented
              value={chartType}
              onChange={(value) => setChartType(value as ChartType)}
              options={[
                {
                  label: '折线图',
                  value: 'line',
                  icon: <LineChartOutlined />,
                },
                {
                  label: '直方图',
                  value: 'column',
                  icon: <BarChartOutlined />,
                },
              ]}
              size="small"
            />
            <Select
              value={selectedYear}
              onChange={handleYearChange}
              style={{ width: 120 }}
              disabled={loading}
            >
              {generateYearOptions().map(year => (
                <Option key={year} value={year}>{year}年</Option>
              ))}
            </Select>
          </div>
        </div>
      }
      extra={
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '12px', color: '#999' }}>全年总支出</div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#cf1322' }}>
            ¥{totalExpense.toFixed(2)}
          </div>
        </div>
      }
    >
      {error && (
        <Alert
          message="加载失败"
          description={error}
          type="error"
          style={{ marginBottom: 16 }}
          showIcon
        />
      )}
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" tip="加载中..." />
        </div>
      ) : chartData.length === 0 && !error ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
          {selectedYear}年暂无支出数据
        </div>
      ) : (
        chartType === 'line' ? (
          <Line {...lineChartConfig} />
        ) : (
          <Column {...columnChartConfig} />
        )
      )}
    </Card>
  );
};

export default YearlyExpenseChart;
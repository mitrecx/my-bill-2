import React, { useEffect, useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Typography, Radio, Select, Spin, Alert } from 'antd';
import dayjs from 'dayjs';
import { BillService } from '../api/services';
import type { MonthlyExpenseTrendResponse, DailyExpenseItem } from '../types/bills';
import { useBillsStore } from '../stores/bills';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { Option } = Select;

const generateYearOptions = () => {
  const currentYear = new Date().getFullYear();
  const years = [] as number[];
  for (let i = currentYear; i >= 2020; i--) years.push(i);
  return years;
};

const generateMonthOptions = () => Array.from({ length: 12 }, (_, i) => i + 1);

const MonthlyExpenseTrendChart: React.FC = () => {
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');
  const { monthlyChartYear, monthlyChartMonth, setMonthlyChartYear, setMonthlyChartMonth, setQueryParams } = useBillsStore();
  const [data, setData] = useState<DailyExpenseItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await BillService.getMonthlyExpenseTrend({ year: monthlyChartYear, month: monthlyChartMonth });
        if (resp.success && resp.data) {
          const payload = resp.data as MonthlyExpenseTrendResponse;
          setData(payload.days || []);
          setTotal(payload.total_month_expense || 0);
        } else {
          throw new Error(resp.message || '获取月度支出趋势失败');
        }
      } catch (e: any) {
        const msg = e?.response?.data?.detail || e?.message || '获取数据失败';
        setError(msg);
        setData([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [monthlyChartYear, monthlyChartMonth]);

  const yearOptions = useMemo(() => generateYearOptions(), []);
  const monthOptions = useMemo(() => generateMonthOptions(), []);

  const option = useMemo(() => {
    const daysInMonth = dayjs(`${monthlyChartYear}-${String(monthlyChartMonth).padStart(2, '0')}-01`).daysInMonth();
    const x: number[] = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    const map = new Map<number, number>();
    data.forEach(d => map.set(d.day, d.amount));
    // 原始值（包含0）
    const yRaw = x.map(day => map.get(day) ?? 0);
    // 对数轴不支持0/负值，这里将0显示为缺失（null），以避免对数计算错误，同时在提示中仍展示为0
    const y = yRaw.map(v => (v > 0 ? v : null));
    const hasPositive = yRaw.some(v => v > 0);

    const series = chartType === 'line'
      ? [{
          name: '日支出',
          type: 'line',
          data: y,
          smooth: false,
          symbol: 'circle',
          connectNulls: true,
          lineStyle: { color: '#cf1322' },
          itemStyle: { color: '#cf1322' },
          areaStyle: { color: 'rgba(207, 19, 34, 0.15)' },
        }]
      : [{
          name: '日支出',
          type: 'bar',
          data: y,
          itemStyle: { color: '#cf1322' },
        }];

    const monthStr = `${monthlyChartYear}-${String(monthlyChartMonth).padStart(2, '0')}`;

    const yAxis = hasPositive
      ? {
          type: 'log' as const,
          logBase: 10,
          min: 'dataMin' as const,
          max: 'dataMax' as const,
          name: '金额（对数刻度）',
          nameLocation: 'middle' as const,
          nameGap: 50,
          axisLabel: {
            formatter: (value: number) => `¥${value}`,
          },
          splitLine: { show: true, lineStyle: { type: 'dashed' } },
        }
      : {
          type: 'value' as const,
          min: 0,
          name: '金额',
          nameLocation: 'middle' as const,
          nameGap: 50,
          axisLabel: { formatter: (value: number) => `¥${value}` },
          splitLine: { show: true, lineStyle: { type: 'dashed' } },
        };

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const p = params && params.length > 0 ? params[0] : null;
          const day = p?.axisValue ?? '';
          const valNum = typeof p?.value === 'number' ? p.value : 0;
          const val = typeof valNum === 'number' ? valNum.toFixed(2) : '0.00';
          const date = dayjs(`${monthStr}-${String(day).padStart(2, '0')}`).format('YYYY-MM-DD');
          return `${date}<br/>日支出: <strong style=\"color:#cf1322\">¥${val}</strong>`;
        },
      },
      legend: { data: ['日支出'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: x, axisTick: { alignWithLabel: true }, name: '日' },
      yAxis,
      series,
    };
  }, [data, chartType, monthlyChartYear, monthlyChartMonth]);

  // 新增：图表点击交互，点击某一天跳转到账单总览并预设日期与支出筛选
  const handleChartClick = (param: any) => {
    try {
      const dayVal = Number(param?.name ?? param?.axisValue ?? (typeof param?.dataIndex === 'number' ? param.dataIndex + 1 : NaN));
      if (!dayVal || Number.isNaN(dayVal)) return;
      const y = monthlyChartYear;
      const m = monthlyChartMonth;
      const date = dayjs(`${y}-${String(m).padStart(2, '0')}-${String(dayVal).padStart(2, '0')}`);

      setQueryParams({
        start_date: date.format('YYYY-MM-DD'),
        end_date: date.format('YYYY-MM-DD'),
        transaction_type: 'expense',
        page: 1,
        size: 10,
      });
      navigate('/bills');
    } catch (err) {
      console.error('处理日点击交互失败: ', err);
    }
  };

  return (
    <Card style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={5} style={{ margin: 0 }}>月度支出趋势</Title>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Radio.Group value={chartType} onChange={(e) => setChartType(e.target.value)}>
            <Radio.Button value="line">折线图</Radio.Button>
            <Radio.Button value="bar">直方图</Radio.Button>
          </Radio.Group>
          <Select value={monthlyChartYear} onChange={setMonthlyChartYear} style={{ width: 120 }}>
            {yearOptions.map(y => <Option key={y} value={y}>{y}年</Option>)}
          </Select>
          <Select value={monthlyChartMonth} onChange={setMonthlyChartMonth} style={{ width: 100 }}>
            {monthOptions.map(m => <Option key={m} value={m}>{m}月</Option>)}
          </Select>
          <div>
            <Text>本月总支出: </Text>
            <Text type="danger" strong>¥{total.toFixed(2)}</Text>
          </div>
          <Text type="secondary">Y轴为对数刻度（0值不显示）</Text>
        </div>
      </div>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
          <Spin size="large" />
        </div>
      ) : error ? (
        <Alert message="错误" description={error} type="error" showIcon />
      ) : (
        <ReactECharts option={option} style={{ height: 300 }} notMerge lazyUpdate onEvents={{ click: handleChartClick }} />
      )}
    </Card>
  );
};

export default MonthlyExpenseTrendChart;
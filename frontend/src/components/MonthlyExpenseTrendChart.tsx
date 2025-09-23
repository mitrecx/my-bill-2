import React, { useEffect, useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Typography, Radio, Select, Spin, Alert } from 'antd';
import dayjs from 'dayjs';
import { BillService } from '../api/services';
import type { MonthlyExpenseTrendResponse, DailyExpenseItem } from '../types/bills';

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
  const now = new Date();
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');
  const [selectedYear, setSelectedYear] = useState<number>(now.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(now.getMonth() + 1);
  const [data, setData] = useState<DailyExpenseItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await BillService.getMonthlyExpenseTrend({ year: selectedYear, month: selectedMonth });
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
  }, [selectedYear, selectedMonth]);

  const yearOptions = useMemo(() => generateYearOptions(), []);
  const monthOptions = useMemo(() => generateMonthOptions(), []);

  const option = useMemo(() => {
    const daysInMonth = dayjs(`${selectedYear}-${String(selectedMonth).padStart(2, '0')}-01`).daysInMonth();
    const x: number[] = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    const map = new Map<number, number>();
    data.forEach(d => map.set(d.day, d.amount));
    const y = x.map(day => map.get(day) ?? 0);

    const series = chartType === 'line'
      ? [{
          name: '日支出',
          type: 'line',
          data: y,
          smooth: false,
          symbol: 'circle',
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

    const monthStr = `${selectedYear}-${String(selectedMonth).padStart(2, '0')}`;

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const p = params[0];
          const day = p?.axisValue ?? '';
          const val = typeof p?.value === 'number' ? p.value.toFixed(2) : '0.00';
          const date = dayjs(`${monthStr}-${String(day).padStart(2, '0')}`).format('YYYY-MM-DD');
          return `${date}<br/>日支出: <strong style="color:#cf1322">¥${val}</strong>`;
        },
      },
      legend: { data: ['日支出'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: x, axisTick: { alignWithLabel: true }, name: '日' },
      yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' }, splitLine: { show: true, lineStyle: { type: 'dashed' } } },
      series,
    };
  }, [data, chartType, selectedYear, selectedMonth]);

  return (
    <Card style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={5} style={{ margin: 0 }}>月度支出趋势</Title>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Radio.Group value={chartType} onChange={(e) => setChartType(e.target.value)}>
            <Radio.Button value="line">折线图</Radio.Button>
            <Radio.Button value="bar">直方图</Radio.Button>
          </Radio.Group>
          <Select value={selectedYear} onChange={setSelectedYear} style={{ width: 120 }}>
            {yearOptions.map(y => <Option key={y} value={y}>{y}年</Option>)}
          </Select>
          <Select value={selectedMonth} onChange={setSelectedMonth} style={{ width: 100 }}>
            {monthOptions.map(m => <Option key={m} value={m}>{m}月</Option>)}
          </Select>
          <div>
            <Text>本月总支出: </Text>
            <Text type="danger" strong>¥{total.toFixed(2)}</Text>
          </div>
        </div>
      </div>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
          <Spin size="large" />
        </div>
      ) : error ? (
        <Alert message="错误" description={error} type="error" showIcon />
      ) : (
        <ReactECharts option={option} style={{ height: 300 }} notMerge lazyUpdate />
      )}
    </Card>
  );
};

export default MonthlyExpenseTrendChart;
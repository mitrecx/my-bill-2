import React, { useEffect, useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Typography, Radio, Select, Spin, Alert } from 'antd';
import dayjs from 'dayjs';
import { BillService } from '../api/services';
import type { CategoryStats } from '../types';
import { useBillsStore } from '../stores/bills';

const { Title, Text } = Typography;
const { Option } = Select;

const generateYearOptions = () => {
  const currentYear = new Date().getFullYear();
  const years: number[] = [];
  for (let i = currentYear; i >= 2020; i--) years.push(i);
  return years;
};

const generateMonthOptions = () => Array.from({ length: 12 }, (_, i) => i + 1);

const MonthlyExpenseCategoryChart: React.FC = () => {
  const [chartType, setChartType] = useState<'pie' | 'bar'>('pie');
  const { monthlyChartYear, monthlyChartMonth, setMonthlyChartYear, setMonthlyChartMonth } = useBillsStore();
  const [data, setData] = useState<CategoryStats[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const start = dayjs(`${monthlyChartYear}-${String(monthlyChartMonth).padStart(2, '0')}-01`);
        const end = start.endOf('month');
        const resp = await BillService.getCategoryStats({
          start_date: start.format('YYYY-MM-DD'),
          end_date: end.format('YYYY-MM-DD'),
        });
        if (resp.success && Array.isArray(resp.data)) {
          const list = (resp.data as CategoryStats[]) || [];
          const sorted = [...list].sort((a, b) => b.total_amount - a.total_amount);
          setData(sorted);
          const sum = sorted.reduce((acc, cur) => acc + (cur.total_amount || 0), 0);
          setTotal(sum);
        } else {
          throw new Error(resp.message || '获取支出分类统计失败');
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
    const names = data.map(d => d.category_name);
    const values = data.map(d => Number(d.total_amount?.toFixed ? d.total_amount.toFixed(2) : d.total_amount));

    if (chartType === 'pie') {
      return {
        tooltip: {
          trigger: 'item',
          formatter: (p: any) => {
            const amt = typeof p.value === 'number' ? p.value.toFixed(2) : p.value;
            return `${p.name}<br/>金额：<strong style="color:#cf1322">¥${amt}</strong><br/>占比：${p.percent}%`;
          },
        },
        legend: {
          type: 'scroll',
          orient: 'horizontal',
          bottom: 0,
        },
        series: [
          {
            name: '分类占比',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 1 },
            label: { formatter: '{b}: {d}%'},
            emphasis: { scale: true },
            data: data.map(d => ({ name: d.category_name, value: d.total_amount })),
          },
        ],
      };
    }

    // bar
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any[]) => {
          const p = params && params[0];
          if (!p) return '';
          const idx = p.dataIndex;
          const name = names[idx];
          const amt = typeof p.value === 'number' ? p.value.toFixed(2) : p.value;
          const pct = total > 0 ? ((values[idx] / total) * 100).toFixed(2) : '0.00';
          return `${name}<br/>金额：<strong style="color:#cf1322">¥${amt}</strong><br/>占比：${pct}%`;
        },
      },
      grid: { left: '3%', right: '4%', bottom: 60, top: 30, containLabel: true },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: { interval: 0, rotate: names.length > 8 ? 30 : 0 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (v: number) => `¥${v}` },
        splitLine: { show: true, lineStyle: { type: 'dashed' } },
      },
      series: [
        {
          name: '支出金额',
          type: 'bar',
          data: values,
          itemStyle: { color: '#cf1322' },
          barMaxWidth: 36,
        },
      ],
    };
  }, [chartType, data, total]);

  return (
    <Card style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={5} style={{ margin: 0 }}>月度支出分类</Title>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Radio.Group value={chartType} onChange={(e) => setChartType(e.target.value)}>
            <Radio.Button value="pie">饼图</Radio.Button>
            <Radio.Button value="bar">直方图</Radio.Button>
          </Radio.Group>
          <Select value={monthlyChartYear} onChange={setMonthlyChartYear} style={{ width: 120 }}>
            {yearOptions.map(y => <Option key={y} value={y}>{y}年</Option>)}
          </Select>
          <Select value={monthlyChartMonth} onChange={setMonthlyChartMonth} style={{ width: 100 }}>
            {monthOptions.map(m => <Option key={m} value={m}>{m}月</Option>)}
          </Select>
          <div>
            <Text>本月分类总支出: </Text>
            <Text type="danger" strong>¥{total.toFixed(2)}</Text>
          </div>
          {chartType === 'bar' ? (
            <Text type="secondary">直方图按金额降序排列</Text>
          ) : (
            <Text type="secondary">悬停查看金额与占比</Text>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 320 }}>
          <Spin size="large" />
        </div>
      ) : error ? (
        <Alert message="错误" description={error} type="error" showIcon />
      ) : data.length === 0 ? (
        <Alert message="暂无数据" type="info" showIcon />
      ) : (
        <ReactECharts option={option} style={{ height: 360 }} notMerge lazyUpdate />
      )}
    </Card>
  );
};

export default MonthlyExpenseCategoryChart;
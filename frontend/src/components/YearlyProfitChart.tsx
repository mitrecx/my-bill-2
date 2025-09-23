import React, { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Radio, Select, Card, Spin, Alert, Typography } from 'antd';
import { BillService } from '../api/services';
import type { YearlyExpenseChartResponse, MonthlyExpenseItem } from '../types/bills';

const { Title, Text } = Typography;
const { Option } = Select;

/**
 * 生成年份选项
 * @returns 年份列表
 */
const generateYearOptions = () => {
  const currentYear = new Date().getFullYear();
  const years = [];
  for (let i = currentYear; i >= 2020; i--) {
    years.push(i);
  }
  return years;
};

const YearlyProfitChart: React.FC = () => {
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [chartData, setChartData] = useState<MonthlyExpenseItem[]>([]);
  const [totalProfit, setTotalProfit] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadChartData = async (year: number) => {
      setLoading(true);
      setError(null);
      try {
        const response = await BillService.getYearlyExpenseChart(year);
        if (response.success && response.data) {
          const data = response.data as YearlyExpenseChartResponse;
          // 计算净收益数据
          const sanitizedData = data.monthly_expenses.map((item: MonthlyExpenseItem) => ({
            ...item,
            amount: item.amount ?? 0,
            income: item.income ?? 0,
            profit: (item.income ?? 0) - (item.amount ?? 0), // 计算净收益
          }));
          setChartData(sanitizedData);
          // 计算全年净收益
          const yearlyProfit = (data.total_year_income ?? 0) - (data.total_year_expense ?? 0);
          setTotalProfit(yearlyProfit);
        } else {
          throw new Error(response.message || '获取年度收益数据失败');
        }
      } catch (e: any) {
        const errorMsg = e?.response?.data?.detail || e?.message || '获取数据失败';
        setError(errorMsg);
        setChartData([]);
        setTotalProfit(0);
      } finally {
        setLoading(false);
      }
    };

    loadChartData(selectedYear);
  }, [selectedYear]);

  const yearOptions = useMemo(() => generateYearOptions(), []);

  const getChartOption = useMemo(() => {
    const profits = chartData.map(item => (item.income ?? 0) - (item.amount ?? 0));
    const positiveArea = profits.map(v => (v > 0 ? v : 0));
    const negativeArea = profits.map(v => (v < 0 ? v : 0));

    const series = chartType === 'line'
      ? [
          // 绿色正收益填充区域（隐藏折线，仅显示面积）
          {
            name: '正收益区域',
            type: 'line',
            data: positiveArea,
            smooth: false,
            symbol: 'none',
            lineStyle: { opacity: 0 },
            areaStyle: { color: 'rgba(82, 196, 26, 0.25)' },
            tooltip: { show: false },
            z: 1,
          },
          // 红色负收益填充区域（隐藏折线，仅显示面积）
          {
            name: '负收益区域',
            type: 'line',
            data: negativeArea,
            smooth: false,
            symbol: 'none',
            lineStyle: { opacity: 0 },
            areaStyle: { color: 'rgba(255, 77, 79, 0.25)' },
            tooltip: { show: false },
            z: 1,
          },
          // 实际净收益折线（位于最上层）
          {
            name: '净收益',
            type: 'line',
            data: profits,
            smooth: false,
            symbol: 'circle',
            itemStyle: {
              color: (params: any) => (params.value >= 0 ? '#009612' : '#C72600'),
            },
            lineStyle: { color: '#666' },
            z: 3,
            markLine: {
              data: [
                {
                  yAxis: 0,
                  lineStyle: { color: '#666', type: 'solid', width: 1 },
                  label: { show: false },
                },
              ],
            },
          },
        ]
      : [
          {
            name: '净收益',
            type: 'bar',
            data: profits,
            itemStyle: {
              color: (params: any) => (params.value >= 0 ? '#009612' : '#C72600'),
            },
            markLine: {
              data: [
                {
                  yAxis: 0,
                  lineStyle: { color: '#666', type: 'solid', width: 1 },
                  label: { show: false },
                },
              ],
            },
          },
        ];

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const p = Array.isArray(params) ? params.find((x: any) => x.seriesName === '净收益') || params[0] : params;
          const value = typeof p.value === 'number' ? p.value.toFixed(2) : '0.00';
          const color = (p.value ?? 0) >= 0 ? '#009612' : '#C72600';
          return `${p.name}<br/>净收益: <strong style="color: ${color}">¥${value}</strong>`;
        },
      },
      legend: {
        data: ['净收益'],
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: chartData.map((item) => item.month_name),
        axisTick: { alignWithLabel: true },
      },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: '¥{value}' },
        splitLine: { show: true, lineStyle: { type: 'dashed' } },
      },
      series,
    };
  }, [chartData, chartType]);

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={5} style={{ margin: 0 }}>年度收益趋势</Title>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Radio.Group value={chartType} onChange={(e) => setChartType(e.target.value)}>
            <Radio.Button value="line">折线图</Radio.Button>
            <Radio.Button value="bar">直方图</Radio.Button>
          </Radio.Group>
          <Select value={selectedYear} onChange={(value) => setSelectedYear(value)} style={{ width: 120 }}>
            {yearOptions.map(year => (
              <Option key={year} value={year}>{year}年</Option>
            ))}
          </Select>
          <div>
            <Text>全年净收益: </Text>
            <Text type={totalProfit >= 0 ? "success" : "danger"} strong>
              ¥{totalProfit.toFixed(2)}
            </Text>
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
        <ReactECharts option={getChartOption} style={{ height: 300 }} notMerge={true} lazyUpdate={true} />
      )}
    </Card>
  );
};

export default YearlyProfitChart;
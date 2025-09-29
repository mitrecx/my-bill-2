import React, { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Radio, Select, Card, Spin, Alert, Typography } from 'antd';
import { SOFT_RED, SOFT_GREEN, SOFT_RED_AREA, SOFT_GREEN_AREA } from '../utils/colors';
import { BillService } from '../api/services';
import type { YearlyExpenseChartResponse, MonthlyExpenseItem } from '../types/bills';
import { useBillsStore } from '../stores/bills';
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { useAuthStore } from '../stores/auth'

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
  // 共享：图表类型、年份
  const chartType = useBillsStore(s => s.yearlyChartType);
  const selectedYear = useBillsStore(s => s.yearlyChartYear);
  const setChartType = useBillsStore(s => s.setYearlyChartType);
  const setSelectedYear = useBillsStore(s => s.setYearlyChartYear);
  const dashboardScope = useBillsStore(s => s.dashboardScope);

  const [chartData, setChartData] = useState<MonthlyExpenseItem[]>([]);
  const [totalProfit, setTotalProfit] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadChartData = async (year: number) => {
      setLoading(true);
      setError(null);
      try {
        const response = await BillService.getYearlyExpenseChart(year, dashboardScope);
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
  }, [selectedYear, dashboardScope]);

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
            areaStyle: undefined,
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
            areaStyle: undefined,
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
              color: (params: any) => (params.value >= 0 ? SOFT_GREEN : SOFT_RED),
            },
            lineStyle: { color: '#722ED1' },
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
              color: (params: any) => (params.value >= 0 ? SOFT_GREEN : SOFT_RED),
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
          const color = (p.value ?? 0) >= 0 ? SOFT_GREEN : SOFT_RED;
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

  // 在组件内部，补充导航与筛选参数设置
  const setQueryParams = useBillsStore(s => s.setQueryParams);
  const resetQueryParams = useBillsStore(s => s.resetQueryParams);
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const handleChartClick = (params: any) => {
    try {
      const index: number | undefined = params?.dataIndex;
      if (index === undefined || index === null) return;
      const item = chartData[index];
      if (!item) return;
      const month = item.month; // 1-12
      const year = selectedYear;
      const start = dayjs(`${year}-${String(month).padStart(2, '0')}-01`);
      const end = start.endOf('month');

      // 清空与当前查询无关的条件，仅保留本次跳转相关参数
      resetQueryParams();
      setQueryParams({
        start_date: start.format('YYYY-MM-DD'),
        end_date: end.format('YYYY-MM-DD'),
        transaction_type: ['income', 'expense'],
        category_id: undefined,
        // 若为个人仪表盘，自动限定为当前用户
        user_id: dashboardScope === 'personal' && user?.id ? user.id : undefined,
        page: 1,
        size: 10,
      });

      navigate('/bills');
    } catch (err) {
      console.error('处理年度收益图点击失败: ', err);
    }
  };

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
        <ReactECharts option={getChartOption} style={{ height: 300 }} notMerge={true} lazyUpdate={true} onEvents={{ click: handleChartClick }} />
      )}
    </Card>
  );
};

export default YearlyProfitChart;
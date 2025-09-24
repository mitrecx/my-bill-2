import React, { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Radio, Select, Card, Spin, Alert, Typography } from 'antd';
import { BillService } from '../api/services';
import type { YearlyExpenseChartResponse, MonthlyExpenseItem } from '../types/bills';
import { useBillsStore } from '../stores/bills';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

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

const YearlyExpenseChart: React.FC = () => {
  // 共享：图表类型、年份
  const chartType = useBillsStore(s => s.yearlyChartType);
  const selectedYear = useBillsStore(s => s.yearlyChartYear);
  const setChartType = useBillsStore(s => s.setYearlyChartType);
  const setSelectedYear = useBillsStore(s => s.setYearlyChartYear);
  const setQueryParams = useBillsStore(s => s.setQueryParams);

  const [chartData, setChartData] = useState<MonthlyExpenseItem[]>([]);
  const [totalExpense, setTotalExpense] = useState<number>(0);
  const [totalIncome, setTotalIncome] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const loadChartData = async (year: number) => {
      setLoading(true);
      setError(null);
      try {
        const response = await BillService.getYearlyExpenseChart(year);
        if (response.success && response.data) {
          const data = response.data as YearlyExpenseChartResponse;
          // ECharts可以很好地处理null/undefined，但我们最好还是做一下清洗
          const sanitizedData = data.monthly_expenses.map((item: MonthlyExpenseItem) => ({
            ...item,
            amount: item.amount ?? 0,
            income: item.income ?? 0,
          }));
          setChartData(sanitizedData);
          setTotalExpense(data.total_year_expense ?? 0);
          setTotalIncome(data.total_year_income ?? 0);
        } else {
          throw new Error(response.message || '获取年度支出数据失败');
        }
      } catch (e: any) {
        const errorMsg = e?.response?.data?.detail || e?.message || '获取数据失败';
        setError(errorMsg);
        setChartData([]);
        setTotalExpense(0);
        setTotalIncome(0);
      } finally {
        setLoading(false);
      }
    };

    loadChartData(selectedYear);
  }, [selectedYear]);

  const yearOptions = useMemo(() => generateYearOptions(), []);

  const getChartOption = useMemo(() => {
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let tooltipContent = `${params[0].name}<br />`;
          params.forEach((param: any) => {
            const value = typeof param.value === 'number' ? param.value.toFixed(2) : '0.00';
            tooltipContent += `${param.marker}${param.seriesName}: <strong>¥${value}</strong><br />`;
          });
          return tooltipContent;
        }
      },
      legend: {
        data: ['支出金额', '收入金额']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.map(item => item.month_name),
        axisTick: {
          alignWithLabel: true
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '¥{value}'
        }
      },
      series: [
        {
          name: '支出金额',
          type: chartType,
          data: chartData.map(item => item.amount),
          smooth: false,
          itemStyle: {
            color: '#C72600' // 支出使用红色
          },
          areaStyle: chartType === 'line' ? {
            color: 'rgba(242, 46, 49, 0.2)'
          } : undefined,
        },
        {
          name: '收入金额',
          type: chartType,
          data: chartData.map(item => item.income),
          smooth: false,
          itemStyle: {
            color: '#009612' // 收入使用绿色
          },
          areaStyle: chartType === 'line' ? {
            color: 'rgba(78, 255, 54, 0.2)'
          } : undefined,
        }
      ]
    };
  }, [chartData, chartType]);

  // 新增：图表点击交互，跳转到账单总览并预设月份查询条件
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

      // 写入全局查询参数：限定日期范围，并预选“收入 + 支出”类型
      setQueryParams({
        start_date: start.format('YYYY-MM-DD'),
        end_date: end.format('YYYY-MM-DD'),
        transaction_type: ['income', 'expense'],
        page: 1,
        size: 10,
      });

      // 跳转到账单总览
      navigate('/bills');
    } catch (err) {
      // 忽略交互错误，避免影响主流程
      console.error('处理图表点击交互失败: ', err);
    }
  };

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={5} style={{ margin: 0 }}>年度收支趋势</Title>
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
            <Text>全年总支出: </Text>
            <Text type="danger" strong>¥{totalExpense.toFixed(2)}</Text>
          </div>
          <div style={{ marginLeft: 16 }}>
            <Text>全年总收入: </Text>
            <Text type="success" strong>¥{totalIncome.toFixed(2)}</Text>
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
        // 绑定点击事件
        <ReactECharts 
          option={getChartOption} 
          style={{ height: 300 }} 
          notMerge={true} 
          lazyUpdate={true}
          onEvents={{ click: handleChartClick }}
        />
      )}
    </Card>
  );
};

export default YearlyExpenseChart;
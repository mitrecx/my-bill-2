export interface MonthlyExpenseItem {
  month: number;
  month_name: string;
  amount: number;
  income: number;
}

export interface YearlyExpenseChartResponse {
  monthly_expenses: MonthlyExpenseItem[];
  total_year_expense: number;
  total_year_income: number;
}

// 新增：日度支出项与月度支出趋势响应
export interface DailyExpenseItem {
  day: number;
  date_str: string; // YYYY-MM-DD
  amount: number;
}

export interface MonthlyExpenseTrendResponse {
  year: number;
  month: number;
  days: DailyExpenseItem[];
  total_month_expense: number;
}
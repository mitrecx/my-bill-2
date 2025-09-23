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
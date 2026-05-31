import React from 'react';
import { Tag } from 'antd';

type TransactionType = 'income' | 'expense' | 'transfer' | string;

const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  income: '收入',
  expense: '支出',
  transfer: '不计收支',
};

const TRANSACTION_TYPE_COLORS: Record<string, string> = {
  income: 'green',
  expense: 'red',
  transfer: 'blue',
};

interface TransactionTypeTagProps {
  type: TransactionType;
}

const TransactionTypeTag: React.FC<TransactionTypeTagProps> = ({ type }) => (
  <Tag color={TRANSACTION_TYPE_COLORS[type] ?? 'default'}>
    {TRANSACTION_TYPE_LABELS[type] ?? type}
  </Tag>
);

export default TransactionTypeTag;

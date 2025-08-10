#!/usr/bin/env python3
"""
分析微信账单文件格式的脚本
"""
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_wechat_bills():
    """分析微信账单文件格式"""
    file_path = "/Users/chenxing/projects/my-bills-2/bills/微信支付账单流水文件(20250501-20250801)_20250810092405.xlsx"
    
    try:
        # 读取Excel文件
        print("正在读取微信账单文件...")
        df = pd.read_excel(file_path)
        
        print(f"文件读取成功！")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        
        # 查找数据开始的行
        data_start_row = None
        for i, row in df.iterrows():
            if str(row.iloc[0]) == "交易时间":
                data_start_row = i
                print(f"\n找到数据标题行在第{i+1}行")
                break
        
        if data_start_row is not None:
            # 重新读取，跳过前面的元数据行
            df_data = pd.read_excel(file_path, skiprows=data_start_row)
            print(f"\n实际数据行数: {len(df_data)}")
            print(f"实际数据列数: {len(df_data.columns)}")
            
            print("\n实际列名:")
            for i, col in enumerate(df_data.columns):
                print(f"{i+1}. {col}")
            
            print("\n前5行实际数据:")
            print(df_data.head())
            
            print("\n数据类型:")
            print(df_data.dtypes)
            
            # 分析每列的数据特征
            print("\n各列数据分析:")
            for col in df_data.columns:
                non_null_count = df_data[col].count()
                unique_count = df_data[col].nunique()
                print(f"{col}: 非空值{non_null_count}个, 唯一值{unique_count}个")
                if non_null_count > 0:
                    sample_values = df_data[col].dropna().head(3).tolist()
                    print(f"  样本值: {sample_values}")
            
            # 保存实际数据到CSV
            data_file = "/Users/chenxing/projects/my-bills-2/tests/wechat_data.csv"
            df_data.to_csv(data_file, index=False, encoding='utf-8-sig')
            print(f"\n实际数据已保存到: {data_file}")
            
            # 分析交易类型
            if '交易类型' in df_data.columns:
                print(f"\n交易类型分布:")
                print(df_data['交易类型'].value_counts())
            
            # 分析收支类型
            if '收/支' in df_data.columns:
                print(f"\n收支类型分布:")
                print(df_data['收/支'].value_counts())
                
        else:
            print("\n未找到数据标题行，显示所有行内容:")
            for i in range(len(df)):
                print(f"第{i+1}行: {df.iloc[i].tolist()}")
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_wechat_bills()
import React, { useState, useEffect } from 'react';
import {
  Typography,
  Upload,
  Button,
  Card,
  Table,
  Space,
  Alert,
  Modal,
  Select,
  Form,
  message,
  Progress,
  Tag,
  Divider,
} from 'antd';
import {
  InboxOutlined,
  // UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
// import { useAuthStore } from '../stores/auth';
import { UploadService, FamilyService } from '../api/services';
import type { Bill, FileUploadResponse, Family } from '../types';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile, UploadProps } from 'antd/es/upload';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

const UploadPage: React.FC = () => {
  // const { user } = useAuthStore();
  const { fetchBills } = useBillsStore();
  
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewData, setPreviewData] = useState<FileUploadResponse | null>(null);
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamily, setSelectedFamily] = useState<number | undefined>();
  const [isConfirmModalVisible, setIsConfirmModalVisible] = useState(false);
  // const [form] = Form.useForm();

  useEffect(() => {
    loadFamilies();
  }, []);

  const loadFamilies = async () => {
    try {
      const familiesData = await FamilyService.getFamilies();
      console.log('[UploadPage] familiesData', familiesData);
      setFamilies(Array.isArray(familiesData.data) ? familiesData.data : []);
      if (Array.isArray(familiesData.data) && familiesData.data.length > 0) {
        setSelectedFamily(familiesData.data[0].id);
      }
    } catch (error) {
      message.error('加载家庭列表失败');
      setFamilies([]);
    }
  };

  // 支持的文件类型和说明
  const supportedFiles = [
    {
      type: '支付宝账单',
      format: 'CSV文件',
      description: '从支付宝APP导出的交易记录CSV文件',
      icon: '💰',
    },
    {
      type: '京东账单',
      format: 'CSV文件', 
      description: '从京东APP导出的交易记录CSV文件',
      icon: '🛒',
    },
    {
      type: '招商银行账单',
      format: 'PDF文件',
      description: '从招商银行APP导出的交易流水PDF文件',
      icon: '🏦',
    },
  ];

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    fileList,
    beforeUpload: (file) => {
      const isValidType = file.type === 'text/csv' || 
                         file.type === 'application/pdf' ||
                         file.name.endsWith('.csv') ||
                         file.name.endsWith('.pdf');
      
      if (!isValidType) {
        message.error('只支持CSV和PDF文件格式');
        return false;
      }

      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过10MB');
        return false;
      }

      setFileList([file]);
      return false; // 阻止自动上传
    },
    onRemove: () => {
      setFileList([]);
      setPreviewData(null);
    },
  };

  // 预览文件
  const handlePreview = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      
      const file = fileList[0].originFileObj as File;
      if (!file) {
        message.warning('文件无效，请重新选择');
        return;
      }
      const response = await UploadService.previewFile(file);
      
      setPreviewData(response.data);
      setIsConfirmModalVisible(true);
      message.success('文件解析成功');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '文件解析失败');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // 确认上传
  const handleConfirmUpload = async () => {
    if (!selectedFamily) {
      message.warning('请选择家庭');
      return;
    }
    if (fileList.length === 0) {
      message.warning('请先选择账单文件');
      return;
    }
    console.log('[UploadPage] fileList[0]', fileList[0]);
    const fileObj = (fileList[0] && (fileList[0].originFileObj as File)) || (fileList[0] as unknown as File);
    if (!fileObj) {
      message.warning('文件无效，请重新选择');
      return;
    }
    try {
      setUploading(true);
      const response = await UploadService.previewFile(fileObj);
      await UploadService.confirmUpload({
        upload_id: response.data.upload_id,
        family_id: selectedFamily,
      });
      message.success('上传成功');
      setFileList([]);
      setPreviewData(null);
      setIsConfirmModalVisible(false);
      fetchBills();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 预览表格列定义
  const previewColumns: ColumnsType<Bill> = [
    {
      title: '交易日期',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '交易描述',
      dataIndex: 'transaction_desc',
      key: 'transaction_desc',
      ellipsis: true,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: Bill) => (
        <span style={{
          color: record.transaction_type === 'income' ? '#3f8600' : '#cf1322',
          fontWeight: 'bold',
        }}>
          {record.transaction_type === 'income' ? '+' : '-'}
          {amount.toFixed(2)}
        </span>
      ),
    },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'income' ? 'green' : 'red'}>
          {type === 'income' ? '收入' : '支出'}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>账单上传</Title>
      
      <Paragraph type="secondary">
        支持上传支付宝、京东、招商银行的账单文件，系统会自动解析并导入账单数据。
      </Paragraph>

      {/* 支持的文件类型说明 */}
      <Card title="支持的文件类型" style={{ marginBottom: 24 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
          {supportedFiles.map((item, index) => (
            <Card key={index} size="small" style={{ border: '1px solid #f0f0f0' }}>
              <Space>
                <span style={{ fontSize: '24px' }}>{item.icon}</span>
                <div>
                  <div style={{ fontWeight: 'bold' }}>{item.type}</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {item.format} • {item.description}
                  </div>
                </div>
              </Space>
            </Card>
          ))}
        </div>
      </Card>

      {/* 家庭选择 */}
      <Card title="选择家庭" style={{ marginBottom: 24 }}>
        <Form layout="inline">
          <Form.Item label="上传到">
            <Select
              value={selectedFamily}
              onChange={setSelectedFamily}
              style={{ width: 200 }}
              placeholder="选择家庭"
            >
              {Array.isArray(families) && families.map(family => (
                <Option key={family.id} value={family.id}>
                  {family.family_name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Card>

      {/* 文件上传区域 */}
      <Card title="上传文件">
        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持CSV和PDF格式，文件大小不超过10MB
          </p>
        </Dragger>

        {uploading && (
          <div style={{ marginBottom: 16 }}>
            <Progress percent={uploadProgress} status="active" />
            <Text type="secondary">正在解析文件...</Text>
          </div>
        )}

        <Space>
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            onClick={handleConfirmUpload}
            disabled={fileList.length === 0 || uploading}
            loading={uploading}
          >
            上传
          </Button>
          
          {fileList.length > 0 && (
            <Button
              onClick={() => {
                setFileList([]);
                setPreviewData(null);
              }}
            >
              清空文件
            </Button>
          )}
        </Space>
      </Card>

      {/* 预览和确认模态框 */}
      <Modal
        title="预览文件内容"
        open={isConfirmModalVisible}
        onCancel={() => setIsConfirmModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setIsConfirmModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="confirm"
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={handleConfirmUpload}
            loading={uploading}
            disabled={!selectedFamily}
          >
            确认上传
          </Button>,
        ]}
        width={800}
        style={{ top: 20 }}
      >
        {previewData && (
          <div>
            <Alert
              message={`解析成功！共找到 ${previewData.total_records} 条记录`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <div style={{ marginBottom: 16 }}>
              <Text strong>文件名：</Text> {previewData.filename}
            </div>

            <Divider>数据预览（前5条）</Divider>

            <Table
              columns={previewColumns}
              dataSource={previewData.preview}
              rowKey="id"
              pagination={false}
              size="small"
              scroll={{ x: 600 }}
            />

            <div style={{ marginTop: 16, padding: 12, background: '#f6f8fa', borderRadius: 6 }}>
              <Space direction="vertical" size="small">
                <Text type="secondary">
                  <ExclamationCircleOutlined /> 注意事项：
                </Text>
                <Text type="secondary">• 确认上传后，数据将被永久保存到选择的家庭账本中</Text>
                <Text type="secondary">• 重复上传相同文件可能导致数据重复</Text>
                <Text type="secondary">• 上传后可在账单管理页面查看和编辑数据</Text>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default UploadPage;
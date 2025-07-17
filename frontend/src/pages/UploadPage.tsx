import React, { useState, useEffect } from 'react';
import {
  Typography,
  Upload,
  Button,
  Card,
  Space,
  Alert,
  Select,
  Form,
  message,
  Progress,
} from 'antd';
import {
  InboxOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
import { UploadService, FamilyService } from '../api/services';
import type { Family } from '../types';
import type { UploadFile, UploadProps } from 'antd/es/upload';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

const UploadPage: React.FC = () => {
  const { fetchBills } = useBillsStore();
  
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamily, setSelectedFamily] = useState<number | undefined>();

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

      // 创建文件列表项，确保包含originFileObj
      const fileItem = {
        uid: file.uid || Date.now().toString(),
        name: file.name,
        status: 'done' as const,
        originFileObj: file,
        size: file.size,
        type: file.type,
      };

      setFileList([fileItem]);
      return false; // 阻止自动上传
    },
    onRemove: () => {
      setFileList([]);
    },
  };

  // 直接上传文件
  const handleUpload = async () => {
    if (!selectedFamily) {
      message.warning('请选择家庭');
      return;
    }
    if (fileList.length === 0) {
      message.warning('请先选择文件');
      return;
    }

    // 获取文件对象，优先使用originFileObj
    const file = fileList[0].originFileObj;
    if (!file) {
      message.warning('文件无效，请重新选择');
      return;
    }

    console.log('上传文件信息:', {
      name: file.name,
      size: file.size,
      type: file.type,
      originFileObj: fileList[0].originFileObj,
      fileListItem: fileList[0]
    });

    try {
      setUploading(true);
      setUploadProgress(0);

      // 使用UploadService.uploadFile方法
      const response = await UploadService.uploadFile(file, selectedFamily);
      
      console.log('上传响应:', response);
      
      // 检查响应结构并安全访问数据
      const uploadData = response.data || response;
      const successCount = uploadData.success_count || 0;
      
      message.success(`上传成功！成功处理 ${successCount} 条记录`);
      setFileList([]);
      setUploadProgress(100);
      fetchBills();
      
    } catch (error: any) {
      console.error('上传错误:', error);
      message.error(error.response?.data?.detail || error.message || '上传失败');
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

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
            <Text type="secondary">正在上传和解析文件...</Text>
          </div>
        )}

        <Space>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleUpload}
            disabled={fileList.length === 0 || uploading || !selectedFamily}
            loading={uploading}
          >
            上传文件
          </Button>
          
          {fileList.length > 0 && (
            <Button
              onClick={() => {
                setFileList([]);
              }}
            >
              清空文件
            </Button>
          )}
        </Space>

        {fileList.length > 0 && (
          <Alert
            message="文件已选择"
            description={`已选择文件：${fileList[0].name}，点击"上传文件"按钮开始上传。`}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    </div>
  );
};

export default UploadPage;
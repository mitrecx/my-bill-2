import React, { useState, useEffect, useRef } from 'react';
import {
  Typography,
  Upload,
  Button,
  Card,
  Space,
  Alert,

  message,
  Progress,
} from 'antd';
import {
  InboxOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useBillsStore } from '../stores/bills';
import { UploadService } from '../api/services';
import type { UploadFile, UploadProps } from 'antd/es/upload';

const { Text, Paragraph } = Typography;
const { Dragger } = Upload;

const UploadPage: React.FC = () => {
  const { fetchBills } = useBillsStore();
  
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState<string>('');
  const progressContainerRef = useRef<HTMLDivElement | null>(null);
  const [showStickyProgress, setShowStickyProgress] = useState(false);

  // 当上传中且内联进度条不在可视区域内时，自动展示悬浮进度条
  useEffect(() => {
    if (!uploading) {
      setShowStickyProgress(false);
      return;
    }
    const node = progressContainerRef.current;
    if (!node) {
      setShowStickyProgress(true);
      return;
    }
    if (typeof window !== 'undefined' && !("IntersectionObserver" in window)) {
      setShowStickyProgress(true);
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0];
      setShowStickyProgress(!entry.isIntersecting);
    }, { threshold: 0.01 });
    observer.observe(node);
    return () => observer.disconnect();
  }, [uploading]);

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
    {
      type: '微信账单',
      format: 'Excel文件',
      description: '从微信APP导出的账单流水Excel文件',
      icon: '💬',
    },
    {
      type: '美团账单',
      format: 'CSV文件',
      description: '从美团APP导出的交易账单CSV文件',
      icon: '🍔',
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
                         file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                         file.type === 'application/vnd.ms-excel' ||
                         file.name.endsWith('.csv') ||
                         file.name.endsWith('.pdf') ||
                         file.name.endsWith('.xlsx') ||
                         file.name.endsWith('.xls');
      
      if (!isValidType) {
        message.error('只支持CSV、PDF和Excel文件格式');
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
      setProgressStatus('正在上传文件...');

      // 使用UploadService.uploadFile方法，传入进度回调
      const response = await UploadService.uploadFile(file, (progress) => {
        // 文件上传进度占总进度的30%
        const uploadProgress = Math.round(progress * 0.3);
        setUploadProgress(uploadProgress);
        setProgressStatus(`正在上传文件... ${progress}%`);
      });
      
      // 文件上传完成，开始解析阶段
      setUploadProgress(30);
      setProgressStatus('文件上传完成，正在解析账单数据...');
      
      console.log('上传响应:', response);
      
      // 检查响应结构并安全访问数据
      const uploadData = response.data || response;
      const successCount = uploadData.success_count || 0;
      const aiClassifiedCount = uploadData.ai_classified_count || 0;
      
      // 模拟解析和处理进度
      setUploadProgress(60); // 解析完成
      setProgressStatus(`账单解析完成，成功处理 ${successCount} 条记录`);
      
      // 如果有AI分类，显示AI分类进度
      if (aiClassifiedCount > 0) {
        setUploadProgress(90); // AI分类完成
        setProgressStatus(`正在进行AI智能分类... 已分类 ${aiClassifiedCount} 条记录`);
      }
      
      let successMessage = `上传成功！成功处理 ${successCount} 条记录`;
      if (aiClassifiedCount > 0) {
        successMessage += `，AI自动分类 ${aiClassifiedCount} 条记录`;
      }
      
      setUploadProgress(100);
      setProgressStatus('处理完成！');
      message.success(successMessage);
      setFileList([]);
      fetchBills();
      
    } catch (error: any) {
      console.error('上传错误:', error);
      
      // 获取后端返回的错误信息
      // 后端使用ApiResponse格式，错误信息在message字段中
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.detail || 
                          error.message || 
                          '上传失败';
      
      // 直接显示后端返回的错误信息，因为后端已经返回了友好的中文错误提示
      message.error(errorMessage);
    } finally {
      setUploading(false);
      setTimeout(() => {
        setUploadProgress(0);
        setProgressStatus('');
      }, 2000);
    }
  };

  return (
    <div>
      
      <Paragraph type="secondary">
        支持上传支付宝、京东、招商银行、微信、美团的账单文件，系统会自动解析并导入账单数据。
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


      {/* 文件上传区域 */}
      <Card title="上传文件">
        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持CSV、PDF和Excel格式，文件大小不超过10MB
          </p>
        </Dragger>

        {uploading && (
          <div ref={progressContainerRef} style={{ marginBottom: 16 }}>
             <Progress 
               percent={uploadProgress} 
               status="active"
               strokeColor={{
                 '0%': '#108ee9',
                 '100%': '#87d068',
               }}
             />
             <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
               <Text type="secondary">{progressStatus}</Text>
               {uploadProgress < 30 && <Text type="secondary">• 文件上传中</Text>}
               {uploadProgress >= 30 && uploadProgress < 60 && <Text type="secondary">• 解析账单数据</Text>}
               {uploadProgress >= 60 && uploadProgress < 90 && <Text type="secondary">• 保存账单记录</Text>}
               {uploadProgress >= 90 && uploadProgress < 100 && <Text type="secondary">• AI智能分类</Text>}
               {uploadProgress === 100 && <Text type="success">• 处理完成</Text>}
             </div>
           </div>
         )}
        {/* 悬浮进度条：当内联进度条不可见时自动显示 */}
        {uploading && showStickyProgress && (
          <div style={{ position: 'fixed', left: '50%', bottom: 16, transform: 'translateX(-50%)', zIndex: 1000, width: 'min(560px, 90vw)' }}>
            <Card size="small" bodyStyle={{ padding: 12 }}>
              <Progress
                percent={uploadProgress}
                status="active"
                strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
              />
              <div style={{ marginTop: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text type="secondary">{progressStatus || '处理中...'}</Text>
                <Text type="secondary">{uploadProgress}%</Text>
              </div>
            </Card>
          </div>
        )}

        <Space>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleUpload}
            disabled={fileList.length === 0 || uploading}
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
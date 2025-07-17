import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout as AntdLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Typography,
  theme,
} from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  UploadOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/auth';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = AntdLayout;
const { Text } = Typography;

const Layout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, loadUser, isAuthenticated } = useAuthStore();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // 确保用户数据在Layout中可用
  useEffect(() => {
    if (isAuthenticated && !user) {
      loadUser().catch(error => {
        console.error('Layout中加载用户数据失败:', error);
      });
    }
  }, [user, loadUser, isAuthenticated]);

  // 菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: 'bills-group',
      icon: <FileTextOutlined />,
      label: '账单管理',
      children: [
        {
          key: '/bills',
          icon: <FileTextOutlined />,
          label: '账单总览',
        },
        {
          key: '/upload',
          icon: <UploadOutlined />,
          label: '导入账单',
        },
      ],
    },
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/stats',
      icon: <BarChartOutlined />,
      label: '统计分析',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ];

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        navigate('/login');
      },
    },
  ];

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
  };

  return (
    <AntdLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div style={{ 
          height: 64, 
          padding: 16, 
          display: 'flex', 
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
        }}>
          <Text 
            strong 
            style={{ 
              color: 'white', 
              fontSize: collapsed ? 14 : 18,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
            }}
          >
            {collapsed ? '账单' : '家庭账单管理'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      
      <AntdLayout>
        <Header style={{ 
          padding: '0 16px', 
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />
          
          <Space>
            <Text>欢迎，{user?.full_name || user?.username}</Text>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar style={{ backgroundColor: '#1890ff', cursor: 'pointer' }}>
                {user?.full_name?.[0] || user?.username?.[0] || 'U'}
              </Avatar>
            </Dropdown>
          </Space>
        </Header>
        
        <Content
          style={{
            margin: '16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: 8,
          }}
        >
          <Outlet />
        </Content>
      </AntdLayout>
    </AntdLayout>
  );
};

export default Layout; 
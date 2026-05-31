import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout as AntdLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  theme,
  Tooltip,
} from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  UploadOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  TeamOutlined,
  FilterOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/auth';
import type { MenuProps } from 'antd';

const { Sider, Content } = AntdLayout;

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

  // 菜单项（根据是否为管理员动态显示“用户管理”和“设置”）
  const baseMenuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '个人仪表板',
    },
    // 新增：家庭仪表板入口
    {
      key: '/family-dashboard',
      icon: <DashboardOutlined />,
      label: '家庭仪表板',
    },
    {
      key: '/bills',
      icon: <FileTextOutlined />,
      label: '账单总览',
    },
    {
      key: 'bills-group',
      icon: <FileTextOutlined />,
      label: '账单管理',
      children: [
        {
          key: '/upload',
          icon: <UploadOutlined />,
          label: '导入账单',
        },
        {
          key: '/classification-rules',
          icon: <FilterOutlined />,
          label: '分类规则',
        },
      ],
    },
    {
      key: '/messages',
      icon: <MessageOutlined />,
      label: '消息中心',
    },
    {
      key: '/family',
      icon: <TeamOutlined />,
      label: '家庭管理',
    },
    {
      key: '/profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: '/mcp-settings',
      icon: <ApiOutlined />,
      label: 'MCP 设置',
    },
  ];

  const adminExtraItems: MenuProps['items'] = [
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const menuItems: MenuProps['items'] = user?.is_admin ? [...baseMenuItems, ...adminExtraItems] : baseMenuItems;

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
  };

  // 用户头像下拉菜单，仅包含退出登录
  const userMenuItems: MenuProps['items'] = [
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

  return (
    <AntdLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div style={{
          padding: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomLeft">
              <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <Avatar style={{ backgroundColor: '#1890ff' }}>
                  {user?.full_name?.[0] || user?.username?.[0] || 'U'}
                </Avatar>
                {!collapsed && (
                  <div style={{ marginLeft: 8, color: '#fff', display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                    <span style={{ fontWeight: 600 }}>{user?.full_name || user?.username || '用户'}</span>
                  </div>
                )}
              </div>
            </Dropdown>
          </div>
        </div>
        <div style={{
          padding: collapsed ? '8px' : '8px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
        }}>
          <Tooltip title={collapsed ? '展开导航' : '收起导航'} placement="right">
            <Button
              onClick={() => setCollapsed(!collapsed)}
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              style={{
                color: '#fff',
                background: 'rgba(255,255,255,0.08)',
                borderRadius: 6,
                transition: 'all .2s ease',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              {!collapsed && <span style={{ marginLeft: 6 }}>收起</span>}
            </Button>
          </Tooltip>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      
      <AntdLayout style={{ height: '100vh', overflow: 'hidden' }}>
        <Content
          style={{
            margin: '0 8px 8px 8px',
            padding: 8,
            background: colorBgContainer,
            borderRadius: 8,
            height: 'calc(100vh - 8px)',
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Outlet />
        </Content>
      </AntdLayout>
    </AntdLayout>
  );
};

export default Layout;
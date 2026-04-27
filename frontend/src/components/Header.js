import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button } from 'antd';
import { LogoutOutlined, LoginOutlined, UserAddOutlined, UserOutlined } from '@ant-design/icons';
import axios from 'axios';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);

    if (!token) {
      setIsAdmin(false);
      return;
    }

    axios.get('/users/me')
      .then((response) => {
        setIsAdmin(response.data.role === 'admin');
      })
      .catch(() => {
        setIsAdmin(false);
      });
  }, [location]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    navigate('/login');
  };

  return (
    <Menu mode="horizontal" theme="dark">
      <Menu.Item key="dashboard">
        <Link to="/dashboard">Главная</Link>
      </Menu.Item>
      <Menu.Item key="appointments">
        <Link to="/appointments">Записи</Link>
      </Menu.Item>
      <Menu.Item key="doctors">
        <Link to="/doctors">Врачи</Link>
      </Menu.Item>
      <Menu.Item key="notifications">
        <Link to="/notifications">Уведомления</Link>
      </Menu.Item>
      <Menu.Item key="classify">
        <Link to="/classify">Классификация</Link>
      </Menu.Item>
      {isAdmin && (
        <Menu.Item key="users">
          <Link to="/users">Пользователи</Link>
        </Menu.Item>
      )}

      <Menu.Item key="auth" style={{ marginLeft: 'auto' }}>
        {isLoggedIn ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button
              type="default"
              icon={<UserOutlined />}
              onClick={() => navigate('/profile')}
            >
              Личный кабинет
            </Button>
            <Button
              type="primary"
              icon={<LogoutOutlined />}
              onClick={handleLogout}
            >
              Выйти
            </Button>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button
              type="link"
              icon={<LoginOutlined />}
              onClick={() => navigate('/login')}
            >
              Войти
            </Button>
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={() => navigate('/register')}
            >
              Регистрация
            </Button>
          </div>
        )}
      </Menu.Item>
    </Menu>
  );
};

export default Header;
import React, { useState, useEffect } from 'react';
import { Card, Typography, message, Spin, Button, Space } from 'antd';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const { Title, Text } = Typography;

const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Требуется авторизация');
        navigate('/login');
        return;
      }

      try {
        const response = await axios.get('/users/me');
        setUser(response.data);
      } catch (error) {
        if (error.response?.status === 401) {
          message.error('Требуется авторизация');
          localStorage.removeItem('token');
          navigate('/login');
        } else {
          message.error('Ошибка загрузки профиля');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 600, margin: 'auto', padding: '20px' }}>
      <Title level={2}>Профиль пользователя</Title>
      {user && (
        <Card>
          <p><Text strong>ФИО:</Text> {user.full_name}</p>
          <p><Text strong>Email:</Text> {user.email}</p>
          <p><Text strong>Телефон:</Text> {user.phone}</p>
          <p><Text strong>Роль:</Text> {user.role || 'user'}</p>
          <p><Text strong>Дата регистрации:</Text> {new Date(user.created_at).toLocaleDateString()}</p>

          {user.role === 'admin' && (
            <div style={{ marginTop: 24 }}>
              <Space>
                <Button type="primary" onClick={() => navigate('/users')}>
                  Управление пользователями
                </Button>
                <Button onClick={() => navigate('/appointments')}>
                  Управление записями
                </Button>
              </Space>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default Profile;
import React, { useState, useEffect } from 'react';
import { Table, message, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUsers();
  }, [navigate]);

  const fetchUsers = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      message.error('Требуется авторизация');
      navigate('/login');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get('/users/all');
      setUsers(response.data);
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        message.error('Требуется доступ администратора');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        message.error('Ошибка загрузки списка пользователей');
      }
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'ФИО', dataIndex: 'full_name', key: 'full_name' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Телефон', dataIndex: 'phone', key: 'phone' },
    { title: 'Роль', dataIndex: 'role', key: 'role' },
    {
      title: 'Дата регистрации',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (value) => (value ? new Date(value).toLocaleString() : '-'),
    },
  ];

  return (
    <div>
      <h1>Пользователи</h1>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={users}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default Users;

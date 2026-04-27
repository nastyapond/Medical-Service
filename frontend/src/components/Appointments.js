import React, { useState, useEffect } from 'react';
import { Table, Button, message, Form, InputNumber, Select, Card, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Appointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCurrentUser();
  }, [navigate]);

  const fetchCurrentUser = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      message.error('Требуется авторизация');
      navigate('/login');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get('/users/me');
      const admin = response.data.role === 'admin';
      setIsAdmin(admin);
      await fetchAppointments(admin, {});
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Требуется авторизация');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        message.error('Ошибка загрузки данных пользователя');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchAppointments = async (admin = isAdmin, filters = {}) => {
    try {
      setLoading(true);
      const url = admin ? '/appointments/all' : '/appointments';
      const response = await axios.get(url, { params: filters });
      setAppointments(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Требуется авторизация');
        localStorage.removeItem('token');
        navigate('/login');
      } else if (error.response?.status === 403) {
        message.error('Требуется доступ администратора');
      } else {
        message.error('Ошибка загрузки записей');
      }
    } finally {
      setLoading(false);
    }
  };

  const onFinish = (values) => {
    const filters = {};
    if (values.patient_id) filters.patient_id = values.patient_id;
    if (values.doctor_id) filters.doctor_id = values.doctor_id;
    if (values.sort_by) filters.sort_by = values.sort_by;
    if (values.sort_order) filters.sort_order = values.sort_order;
    fetchAppointments(true, filters);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Пациент', dataIndex: 'user_id', key: 'user_id' },
    { title: 'Врач', dataIndex: 'doctor_id', key: 'doctor_id' },
    {
      title: 'Дата',
      dataIndex: 'appointment_date',
      key: 'appointment_date',
      render: (value) => (value ? new Date(value).toLocaleString() : '-'),
    },
    { title: 'Статус', dataIndex: 'status', key: 'status' },
  ];

  return (
    <div>
      <h1>{isAdmin ? 'Все записи' : 'Мои записи'}</h1>

      {isAdmin && (
        <Card style={{ marginBottom: 20 }}>
          <Form
            form={form}
            layout="inline"
            onFinish={onFinish}
            initialValues={{ sort_by: 'appointment_date', sort_order: 'asc' }}
          >
            <Form.Item name="patient_id" label="ID пациента">
              <InputNumber min={1} />
            </Form.Item>
            <Form.Item name="doctor_id" label="ID врача">
              <InputNumber min={1} />
            </Form.Item>
            <Form.Item name="sort_by" label="Сортировать по">
              <Select style={{ width: 180 }}>
                <Select.Option value="appointment_date">Дата</Select.Option>
                <Select.Option value="user_id">Пациент</Select.Option>
                <Select.Option value="doctor_id">Врач</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="sort_order" label="Порядок">
              <Select style={{ width: 140 }}>
                <Select.Option value="asc">По возрастанию</Select.Option>
                <Select.Option value="desc">По убыванию</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">
                Применить
              </Button>
            </Form.Item>
            <Form.Item>
              <Button onClick={() => {
                form.resetFields();
                fetchAppointments(true, {});
              }}>
                Сбросить
              </Button>
            </Form.Item>
          </Form>
        </Card>
      )}

      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={appointments}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default Appointments;
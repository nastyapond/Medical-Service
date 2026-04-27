import React, { useState } from 'react';
import { Form, Input, Button, message, Card, Typography } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const { Title } = Typography;

const Register = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await axios.post('/auth/register', values);
      message.success('Регистрация успешна! Теперь войдите в систему.');
      navigate('/login');
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errorMessage = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('; ')
          : error.response?.data?.detail || error.message;
      message.error('Ошибка регистрации: ' + errorMessage);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card style={{ width: 400 }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
          Регистрация
        </Title>
        <Form
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="full_name"
            label="ФИО"
            rules={[
              { required: true, message: 'Введите ФИО' },
              { min: 2, message: 'ФИО должно содержать минимум 2 символа' }
            ]}
          >
            <Input placeholder="Иванов Иван Иванович" />
          </Form.Item>
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Введите email' },
              { type: 'email', message: 'Введите корректный email' }
            ]}
          >
            <Input placeholder="your@email.com" />
          </Form.Item>
          <Form.Item
            name="phone"
            label="Телефон"
            rules={[
              { required: true, message: 'Введите телефон' },
              { pattern: /^\+\d{10,15}$/, message: 'Введите телефон в формате +71234567890' }
            ]}
          >
            <Input placeholder="+7XXXXXXXXXX" />
          </Form.Item>
          <Form.Item
            name="password"
            label="Пароль"
            rules={[
              { required: true, message: 'Введите пароль' },
              { min: 6, message: 'Пароль должен содержать минимум 6 символов' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value) {
                    return Promise.resolve();
                  }
                  if (!/[0-9]/.test(value)) {
                    return Promise.reject(new Error('Пароль должен содержать хотя бы одну цифру'));
                  }
                  if (!/[A-Z]/.test(value)) {
                    return Promise.reject(new Error('Пароль должен содержать хотя бы одну заглавную букву'));
                  }
                  return Promise.resolve();
                }
              })
            ]}
          >
            <Input.Password placeholder="Пароль" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              Зарегистрироваться
            </Button>
          </Form.Item>
          <Form.Item style={{ textAlign: 'center', marginBottom: 0 }}>
            <span>Уже есть аккаунт? </span>
            <Link to="/login">Войти</Link>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Register;
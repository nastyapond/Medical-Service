import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import axios from 'axios';

const { TextArea } = Input;

const Classify = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/classify', values);
      setResult(response.data);
      message.success('Классификация выполнена');
    } catch (error) {
      setResult(null);
      const detail = error.response?.data?.detail;
      const errorMessage = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('; ')
          : error.response?.data?.detail || error.message || 'Ошибка классификации';
      message.error(errorMessage);
    }
    setLoading(false);
  };

  return (
    <div>
      <h1>Классификация обращения</h1>
      <Form onFinish={onFinish} style={{ maxWidth: 600, margin: 'auto' }}>
        <Form.Item name="text" rules={[{ required: true, message: 'Введите текст обращения' }]}>
          <TextArea rows={4} placeholder="Опишите ваше обращение" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Классифицировать
          </Button>
        </Form.Item>
      </Form>
      {result && (
        <Card title="Результат классификации" style={{ marginTop: 20 }}>
          <p><strong>Срочность:</strong> {result.urgency}</p>
          <p><strong>Тип обращения:</strong> {result.request_type}</p>
          <p><strong>Уверенность:</strong> {result.confidence}</p>
        </Card>
      )}
    </div>
  );
};

export default Classify;
import React, { useState, useEffect } from 'react';
import { List, Button, message, Modal, Form, DatePicker, Space, Typography, Card, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const { Title, Text } = Typography;

const Doctors = () => {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [bookingForm] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/doctors');
      setDoctors(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Требуется авторизация');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        message.error('Ошибка загрузки врачей');
      }
    } finally {
      setLoading(false);
    }
  };

  const openBooking = (doctor) => {
    setSelectedDoctor(doctor);
    bookingForm.resetFields();
    setModalVisible(true);
  };

  const handleBooking = async (values) => {
    if (!selectedDoctor) {
      return;
    }

    try {
      setLoading(true);
      await axios.post('/appointments', {
        doctor_id: selectedDoctor.id,
        appointment_date: values.appointment_date.toISOString(),
      });
      message.success(`Вы успешно записаны к врачу ${selectedDoctor.full_name}`);
      setModalVisible(false);
      bookingForm.resetFields();
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Требуется авторизация');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        message.error('Ошибка при записи на прием');
      }
    } finally {
      setLoading(false);
    }
  };

  const disabledDate = (current) => {
    if (!current) {
      return false;
    }
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return current.toDate() < today;
  };

  return (
    <div style={{ maxWidth: 900, margin: 'auto', padding: 20 }}>
      <Title level={2}>Врачи</Title>
      <Card style={{ marginBottom: 20 }}>
        <Text>Выберите врача и запишитесь на удобное время. Все записи будут сохраняться в личном кабинете.</Text>
      </Card>
      <Spin spinning={loading}>
        <List
          dataSource={doctors}
          itemLayout="vertical"
          locale={{ emptyText: 'Врачи не найдены' }}
          renderItem={(item) => (
            <List.Item
              key={item.id}
              actions={[
                <Button type="primary" onClick={() => openBooking(item)}>
                  Записаться
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={`${item.full_name} — ${item.specialization}`}
                description={item.schedule ? `Расписание: ${item.schedule}` : 'Расписание не указано'}
              />
            </List.Item>
          )}
        />
      </Spin>

      <Modal
        title={selectedDoctor ? `Запись к врачу ${selectedDoctor.full_name}` : 'Запись к врачу'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={bookingForm} layout="vertical" onFinish={handleBooking}>
          <Form.Item
            name="appointment_date"
            label="Дата и время"
            rules={[{ required: true, message: 'Выберите дату и время' }]}
          >
            <DatePicker showTime format="YYYY-MM-DD HH:mm" style={{ width: '100%' }} disabledDate={disabledDate} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Записаться
              </Button>
              <Button onClick={() => setModalVisible(false)}>Отмена</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Doctors;
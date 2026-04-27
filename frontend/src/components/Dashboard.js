import React from 'react';
import { Card, Row, Col } from 'antd';

const Dashboard = () => {
  return (
    <div>
      <h1>Медицинский сервис</h1>
      <Row gutter={16}>
        <Col span={8}>
          <Card title="Запись к врачу" bordered={false}>
            Запишитесь на прием к врачу
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Расписание врачей" bordered={false}>
            Просмотрите доступное время
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Уведомления" bordered={false}>
            Ваши напоминания и сообщения
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
import React, { useState, useEffect } from 'react';
import { List } from 'antd';
import axios from 'axios';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get('/notifications');
      setNotifications(response.data);
    } catch (error) {
      console.error('Ошибка загрузки уведомлений');
    }
  };

  return (
    <div>
      <h1>Уведомления</h1>
      <List
        dataSource={notifications}
        renderItem={item => (
          <List.Item>
            {item.text} - {item.sent_at}
          </List.Item>
        )}
      />
    </div>
  );
};

export default Notifications;
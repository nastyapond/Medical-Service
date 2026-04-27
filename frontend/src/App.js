import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import axios from 'axios';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Appointments from './components/Appointments';
import Doctors from './components/Doctors';
import Notifications from './components/Notifications';
import Classify from './components/Classify';
import Profile from './components/Profile';
import Users from './components/Users';
import Header from './components/Header';

const { Content } = Layout;

// Configure axios
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

function App() {
  return (
    <Router>
      <Layout>
        <Header />
        <Content style={{ padding: '0 50px' }}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/appointments" element={<Appointments />} />
            <Route path="/doctors" element={<Doctors />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/classify" element={<Classify />} />
            <Route path="/users" element={<Users />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
}

export default App;
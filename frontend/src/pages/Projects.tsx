import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Space,
  Input,
  Tag,
  Modal,
  Form,
  DatePicker,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Typography,
} from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { projectsApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { getStatusColor, getStatusText } from '../utils';
import type { Project, ProjectStatus } from '../types';

const { Title } = Typography;
const { TextArea } = Input;

export const Projects: React.FC = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();

  const canCreate = hasPermission(['market']);
  const canEdit = hasPermission(['market', 'engineering']);
  const canDelete = hasPermission(['market']);

  const { data, isLoading } = useQuery({
    queryKey: ['projects', page, search],
    queryFn: () => projectsApi.list(page, 20, search || undefined),
  });

  const createMutation = useMutation({
    mutationFn: (values: Partial<Project>) => projectsApi.create(values),
    onSuccess: () => {
      message.success('Project created successfully');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('Failed to create project'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) => projectsApi.update(id, data),
    onSuccess: () => {
      message.success('Project updated successfully');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setModalOpen(false);
      setEditingProject(null);
      form.resetFields();
    },
    onError: () => message.error('Failed to update project'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      message.success('Project deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: () => message.error('Failed to delete project'),
  });

  const handleOpenModal = (project?: Project) => {
    if (project) {
      setEditingProject(project);
      form.setFieldsValue({
        ...project,
        contract_start_date: project.contract_start_date ? dayjs(project.contract_start_date) : null,
        contract_end_date: project.contract_end_date ? dayjs(project.contract_end_date) : null,
        actual_start_date: project.actual_start_date ? dayjs(project.actual_start_date) : null,
      });
    } else {
      setEditingProject(null);
      form.resetFields();
    }
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    const data = {
      ...values,
      contract_start_date: values.contract_start_date?.format('YYYY-MM-DD'),
      contract_end_date: values.contract_end_date?.format('YYYY-MM-DD'),
      actual_start_date: values.actual_start_date?.format('YYYY-MM-DD'),
    };

    if (editingProject) {
      updateMutation.mutate({ id: editingProject.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const columns = [
    {
      title: 'Project Code',
      dataIndex: 'project_code',
      key: 'project_code',
      width: 120,
    },
    {
      title: 'Project Name',
      dataIndex: 'project_name',
      key: 'project_name',
      ellipsis: true,
    },
    {
      title: 'Construction Unit',
      dataIndex: 'construction_unit',
      key: 'construction_unit',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: ProjectStatus) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: 'Contract Duration',
      dataIndex: 'contract_duration',
      key: 'contract_duration',
      width: 120,
      render: (days: number) => (days ? `${days} days` : '-'),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: Project) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/projects/${record.id}`)}
          />
          {canEdit && (
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          )}
          {canDelete && (
            <Popconfirm
              title="Delete this project?"
              onConfirm={() => deleteMutation.mutate(record.id)}
            >
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>Projects</Title>
        <Space>
          <Input
            placeholder="Search projects..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 250 }}
          />
          {canCreate && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              New Project
            </Button>
          )}
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data?.items}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.total,
          onChange: setPage,
        }}
      />

      <Modal
        title={editingProject ? 'Edit Project' : 'New Project'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingProject(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="project_code"
            label="Project Code"
            rules={[{ required: true, message: 'Please input project code' }]}
          >
            <Input disabled={!!editingProject} />
          </Form.Item>

          <Form.Item
            name="project_name"
            label="Project Name"
            rules={[{ required: true, message: 'Please input project name' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item name="construction_unit" label="Construction Unit">
            <Input />
          </Form.Item>

          <Form.Item name="location" label="Location">
            <Input />
          </Form.Item>

          <Space style={{ display: 'flex' }} size="large">
            <Form.Item name="contract_start_date" label="Contract Start Date">
              <DatePicker />
            </Form.Item>
            <Form.Item name="contract_end_date" label="Contract End Date">
              <DatePicker />
            </Form.Item>
            <Form.Item name="actual_start_date" label="Actual Start Date">
              <DatePicker />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }} size="large">
            <Form.Item name="contract_duration" label="Contract Duration (days)">
              <InputNumber min={1} />
            </Form.Item>
            <Form.Item name="status" label="Status" initialValue="planning">
              <Select style={{ width: 150 }}>
                <Select.Option value="planning">Planning</Select.Option>
                <Select.Option value="in_progress">In Progress</Select.Option>
                <Select.Option value="completed">Completed</Select.Option>
                <Select.Option value="suspended">Suspended</Select.Option>
              </Select>
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};

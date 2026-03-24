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
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, EyeOutlined, PaperClipOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { projectsApi } from '../services/api';
import { ExcelImportModal } from '../components/ExcelImportModal';
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
  const canView = hasPermission(['market','engineering']);

  const { data, isLoading } = useQuery({
    queryKey: ['projects', page, search],
    queryFn: () => projectsApi.list(page, 20, search || undefined),
  });

  const createMutation = useMutation({
    mutationFn: (values: Partial<Project>) => projectsApi.create(values),
    onSuccess: () => {
      message.success('项目创建成功');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('项目创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) => projectsApi.update(id, data),
    onSuccess: () => {
      message.success('项目更新成功');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setModalOpen(false);
      setEditingProject(null);
      form.resetFields();
    },
    onError: () => message.error('项目更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      message.success('项目删除成功');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: () => message.error('项目删除失败'),
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
      title: '项目编号',
      dataIndex: 'project_code',
      key: 'project_code',
      width: 120,
    },
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
      ellipsis: true,
    },
    {
      title: '施工单位',
      dataIndex: 'construction_unit',
      key: 'construction_unit',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: ProjectStatus) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '合同工期',
      dataIndex: 'contract_duration',
      key: 'contract_duration',
      width: 120,
      render: (days: number) => (days ? `${days}天` : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: unknown, record: Project) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/projects/${record.id}`)}
          />
          {/* 新增：附件按钮 */}
          {canView && (
            <Button
              type="link"
              icon={<PaperClipOutlined />}
              onClick={() => navigate(`/projects/${record.id}/attachments`)} // 跳转到附件子页面
              
            />
          )}
          {canEdit && (
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          )}
          {canDelete && (
            <Popconfirm
              title="确定删除该项目？"
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
        <Title level={4}>项目管理</Title>
        <Space>
          <Input
            placeholder="搜索项目..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 250 }}
          />
          {canCreate && <ExcelImportModal dataType="project" />}
          {canCreate && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新建项目
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
        title={editingProject ? '编辑项目' : '新建项目'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingProject(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={700}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="project_code"
            label="项目编号"
            rules={[{ required: true, message: '请输入项目编号' }]}
          >
            <Input disabled={!!editingProject} />
          </Form.Item>

          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="description" label="项目描述">
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item name="construction_unit" label="施工单位">
            <Input />
          </Form.Item>

          <Form.Item name="location" label="项目地址">
            <Input />
          </Form.Item>

          <Space style={{ display: 'flex' }} size="large">
            <Form.Item name="contract_start_date" label="合同开始日期">
              <DatePicker />
            </Form.Item>
            <Form.Item name="contract_end_date" label="合同结束日期">
              <DatePicker />
            </Form.Item>
            <Form.Item name="actual_start_date" label="实际开始日期">
              <DatePicker />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }} size="large">
            <Form.Item name="contract_duration" label="合同工期（天）">
              <InputNumber min={1} />
            </Form.Item>
            <Form.Item name="status" label="项目状态" initialValue="planning">
              <Select style={{ width: 150 }}>
                <Select.Option value="planning">规划中</Select.Option>
                <Select.Option value="in_progress">进行中</Select.Option>
                <Select.Option value="completed">已完成</Select.Option>
                <Select.Option value="suspended">已暂停</Select.Option>
              </Select>
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};

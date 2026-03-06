import React, { useState } from 'react';
import { Table, Select, Card, Typography, Space, Spin, Button, Modal, Form, InputNumber, Input, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, financeApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatCurrency } from '../utils';
import type { FinanceData } from '../types';

const { Title } = Typography;
const { TextArea } = Input;

export const FinancePage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | undefined>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingData, setEditingData] = useState<FinanceData | null>(null);
  const [form] = Form.useForm();
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();

  const canEdit = hasPermission(['finance']);

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: financeData, isLoading: dataLoading } = useQuery({
    queryKey: ['financeData', selectedProject],
    queryFn: () => financeApi.list(selectedProject!),
    enabled: !!selectedProject,
  });

  const createMutation = useMutation({
    mutationFn: (values: Partial<FinanceData>) => financeApi.create(selectedProject!, values),
    onSuccess: () => {
      message.success('数据创建成功');
      queryClient.invalidateQueries({ queryKey: ['financeData', selectedProject] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('数据创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<FinanceData> }) =>
      financeApi.update(selectedProject!, id, data),
    onSuccess: () => {
      message.success('数据更新成功');
      queryClient.invalidateQueries({ queryKey: ['financeData', selectedProject] });
      setModalOpen(false);
      setEditingData(null);
      form.resetFields();
    },
    onError: () => message.error('数据更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => financeApi.delete(selectedProject!, id),
    onSuccess: () => {
      message.success('数据删除成功');
      queryClient.invalidateQueries({ queryKey: ['financeData', selectedProject] });
    },
    onError: () => message.error('数据删除失败'),
  });

  const handleOpenModal = (record?: FinanceData) => {
    if (record) {
      setEditingData(record);
      form.setFieldsValue(record);
    } else {
      setEditingData(null);
      form.resetFields();
      form.setFieldsValue({ year: new Date().getFullYear(), month: new Date().getMonth() + 1 });
    }
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingData) {
      updateMutation.mutate({ id: editingData.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const columns = [
    { title: '年份', dataIndex: 'year', width: 80 },
    { title: '月份', dataIndex: 'month', width: 80 },
    { title: '月营收', dataIndex: 'monthly_revenue', render: (v: number) => formatCurrency(v) },
    { title: '月成本', dataIndex: 'monthly_cost', render: (v: number) => formatCurrency(v) },
    { title: '月回款', dataIndex: 'monthly_payment_received', render: (v: number) => formatCurrency(v) },
    { title: '目标毛利率', dataIndex: 'target_margin', render: (v: number) => v ? `${v}%` : '-' },
    { title: '备注', dataIndex: 'remarks', ellipsis: true },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: FinanceData) =>
        canEdit && (
          <Space>
            <Button type="link" icon={<EditOutlined />} onClick={() => handleOpenModal(record)} />
            <Popconfirm title="确定删除该条目？" onConfirm={() => deleteMutation.mutate(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>财务数据</Title>
        {selectedProject && canEdit && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            新增数据
          </Button>
        )}
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>选择项目：</span>
          <Select
            style={{ width: 400 }}
            placeholder="请选择项目"
            loading={projectsLoading}
            value={selectedProject}
            onChange={setSelectedProject}
            showSearch
            optionFilterProp="children"
          >
            {projects?.items.map(p => (
              <Select.Option key={p.id} value={p.id}>
                {p.project_code} - {p.project_name}
              </Select.Option>
            ))}
          </Select>
        </Space>
      </Card>

      {selectedProject ? (
        <Card>
          {dataLoading ? (
            <div style={{ textAlign: 'center', padding: 50 }}>
              <Spin />
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={financeData}
              rowKey="id"
              size="small"
              scroll={{ x: 1000 }}
            />
          )}
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>
            请选择项目查看财务数据
          </div>
        </Card>
      )}

      <Modal
        title={editingData ? '编辑财务数据' : '新增财务数据'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingData(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Space style={{ display: 'flex' }}>
            <Form.Item name="year" label="年份" rules={[{ required: true, message: '请选择年份' }]}>
              <InputNumber min={2000} max={2100} disabled={!!editingData} />
            </Form.Item>
            <Form.Item name="month" label="月份" rules={[{ required: true, message: '请选择月份' }]}>
              <Select style={{ width: 100 }} disabled={!!editingData}>
                {[...Array(12)].map((_, i) => (
                  <Select.Option key={i + 1} value={i + 1}>{i + 1}月</Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="monthly_revenue" label="月营收">
              <InputNumber min={0} precision={2} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="monthly_cost" label="月成本">
              <InputNumber min={0} precision={2} style={{ width: 180 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="monthly_payment_received" label="月回款">
              <InputNumber min={0} precision={2} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="target_margin" label="目标毛利率 %">
              <InputNumber min={0} max={100} precision={2} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          <Form.Item name="remarks" label="备注">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

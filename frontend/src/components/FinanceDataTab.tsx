import React, { useState } from 'react';
import { Table, Button, Modal, Form, InputNumber, Input, Select, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { financeApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatCurrency } from '../utils';
import type { FinanceData } from '../types';

const { TextArea } = Input;

interface Props {
  projectId: string;
  data: FinanceData[];
}

export const FinanceDataTab: React.FC<Props> = ({ projectId, data }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingData, setEditingData] = useState<FinanceData | null>(null);
  const [form] = Form.useForm();
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();

  const canEdit = hasPermission(['finance']);

  const createMutation = useMutation({
    mutationFn: (values: Partial<FinanceData>) => financeApi.create(projectId, values),
    onSuccess: () => {
      message.success('Data created successfully');
      queryClient.invalidateQueries({ queryKey: ['financeData', projectId] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('Failed to create data'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<FinanceData> }) =>
      financeApi.update(projectId, id, data),
    onSuccess: () => {
      message.success('Data updated successfully');
      queryClient.invalidateQueries({ queryKey: ['financeData', projectId] });
      setModalOpen(false);
      setEditingData(null);
      form.resetFields();
    },
    onError: () => message.error('Failed to update data'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => financeApi.delete(projectId, id),
    onSuccess: () => {
      message.success('Data deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['financeData', projectId] });
    },
    onError: () => message.error('Failed to delete data'),
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
    { title: 'Year', dataIndex: 'year', width: 80 },
    { title: 'Month', dataIndex: 'month', width: 80 },
    { title: 'Monthly Revenue', dataIndex: 'monthly_revenue', render: (v: number) => formatCurrency(v) },
    { title: 'Monthly Cost', dataIndex: 'monthly_cost', render: (v: number) => formatCurrency(v) },
    { title: 'Payment Received', dataIndex: 'monthly_payment_received', render: (v: number) => formatCurrency(v) },
    { title: 'Target Margin %', dataIndex: 'target_margin', render: (v: number) => v ? `${v}%` : '-' },
    { title: 'Remarks', dataIndex: 'remarks', ellipsis: true },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: FinanceData) =>
        canEdit && (
          <Space>
            <Button type="link" icon={<EditOutlined />} onClick={() => handleOpenModal(record)} />
            <Popconfirm title="Delete this entry?" onConfirm={() => deleteMutation.mutate(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        ),
    },
  ];

  return (
    <div>
      {canEdit && (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          style={{ marginBottom: 16 }}
        >
          Add Entry
        </Button>
      )}

      <Table columns={columns} dataSource={data} rowKey="id" size="small" scroll={{ x: 1000 }} />

      <Modal
        title={editingData ? 'Edit Finance Data' : 'Add Finance Data'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingData(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Space style={{ display: 'flex' }}>
            <Form.Item name="year" label="Year" rules={[{ required: true }]}>
              <InputNumber min={2000} max={2100} disabled={!!editingData} />
            </Form.Item>
            <Form.Item name="month" label="Month" rules={[{ required: true }]}>
              <Select style={{ width: 100 }} disabled={!!editingData}>
                {[...Array(12)].map((_, i) => (
                  <Select.Option key={i + 1} value={i + 1}>{i + 1}</Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="monthly_revenue" label="Monthly Revenue">
              <InputNumber min={0} precision={2} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="monthly_cost" label="Monthly Cost">
              <InputNumber min={0} precision={2} style={{ width: 180 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="monthly_payment_received" label="Payment Received">
              <InputNumber min={0} precision={2} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="target_margin" label="Target Margin %">
              <InputNumber min={0} max={100} precision={2} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          <Form.Item name="remarks" label="Remarks">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

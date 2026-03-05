import React, { useState } from 'react';
import { Table, Button, Modal, Form, InputNumber, Input, Select, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { engineeringApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatCurrency, formatNumber } from '../utils';
import type { EngineeringData } from '../types';

const { TextArea } = Input;

interface Props {
  projectId: string;
  data: EngineeringData[];
}

export const EngineeringDataTab: React.FC<Props> = ({ projectId, data }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingData, setEditingData] = useState<EngineeringData | null>(null);
  const [form] = Form.useForm();
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();

  const canEdit = hasPermission(['engineering']);

  const createMutation = useMutation({
    mutationFn: (values: Partial<EngineeringData>) => engineeringApi.create(projectId, values),
    onSuccess: () => {
      message.success('Data created successfully');
      queryClient.invalidateQueries({ queryKey: ['engineeringData', projectId] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('Failed to create data'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EngineeringData> }) =>
      engineeringApi.update(projectId, id, data),
    onSuccess: () => {
      message.success('Data updated successfully');
      queryClient.invalidateQueries({ queryKey: ['engineeringData', projectId] });
      setModalOpen(false);
      setEditingData(null);
      form.resetFields();
    },
    onError: () => message.error('Failed to update data'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => engineeringApi.delete(projectId, id),
    onSuccess: () => {
      message.success('Data deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['engineeringData', projectId] });
    },
    onError: () => message.error('Failed to delete data'),
  });

  const handleOpenModal = (record?: EngineeringData) => {
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
    { title: 'Actual Duration', dataIndex: 'actual_duration', render: (v: number) => v ? `${v} days` : '-' },
    { title: 'Progress', dataIndex: 'end_period_progress', ellipsis: true },
    { title: 'Contract Value', dataIndex: 'contract_value', render: (v: number) => formatCurrency(v) },
    { title: 'Monthly Output', dataIndex: 'monthly_output', render: (v: number) => formatCurrency(v) },
    { title: 'Planned Output', dataIndex: 'planned_output', render: (v: number) => formatCurrency(v) },
    { title: 'Monthly Approval', dataIndex: 'monthly_approval', render: (v: number) => formatCurrency(v) },
    { title: 'Staff', dataIndex: 'staff_count', render: (v: number) => formatNumber(v, 0) },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: EngineeringData) =>
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

      <Table columns={columns} dataSource={data} rowKey="id" size="small" scroll={{ x: 1400 }} />

      <Modal
        title={editingData ? 'Edit Engineering Data' : 'Add Engineering Data'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingData(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={700}
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
            <Form.Item name="actual_duration" label="Actual Duration (days)">
              <InputNumber min={0} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          <Form.Item name="end_period_progress" label="End Period Progress">
            <Input />
          </Form.Item>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="contract_value" label="Contract Value">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="monthly_output" label="Monthly Output">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="planned_output" label="Planned Output">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="monthly_approval" label="Monthly Approval">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="staff_count" label="Staff Count">
              <InputNumber min={0} style={{ width: 100 }} />
            </Form.Item>
            <Form.Item name="next_month_plan" label="Next Month Plan">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
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

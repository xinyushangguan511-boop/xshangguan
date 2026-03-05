import React, { useState } from 'react';
import { Table, Button, Modal, Form, InputNumber, Input, Select, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { marketApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatCurrency, formatNumber } from '../utils';
import type { MarketData } from '../types';

const { TextArea } = Input;

interface Props {
  projectId: string;
  data: MarketData[];
}

export const MarketDataTab: React.FC<Props> = ({ projectId, data }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingData, setEditingData] = useState<MarketData | null>(null);
  const [form] = Form.useForm();
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();

  const canEdit = hasPermission(['market']);

  const createMutation = useMutation({
    mutationFn: (values: Partial<MarketData>) => marketApi.create(projectId, values),
    onSuccess: () => {
      message.success('Data created successfully');
      queryClient.invalidateQueries({ queryKey: ['marketData', projectId] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('Failed to create data'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MarketData> }) =>
      marketApi.update(projectId, id, data),
    onSuccess: () => {
      message.success('Data updated successfully');
      queryClient.invalidateQueries({ queryKey: ['marketData', projectId] });
      setModalOpen(false);
      setEditingData(null);
      form.resetFields();
    },
    onError: () => message.error('Failed to update data'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => marketApi.delete(projectId, id),
    onSuccess: () => {
      message.success('Data deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['marketData', projectId] });
    },
    onError: () => message.error('Failed to delete data'),
  });

  const handleOpenModal = (record?: MarketData) => {
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
    { title: 'Building Area (m²)', dataIndex: 'building_area', render: (v: number) => formatNumber(v) },
    { title: 'Structure', dataIndex: 'structure' },
    { title: 'Floors', dataIndex: 'floors' },
    { title: 'Contract Value', dataIndex: 'contract_value', render: (v: number) => formatCurrency(v) },
    { title: 'Prepayment %', dataIndex: 'prepayment_ratio', render: (v: number) => v ? `${v}%` : '-' },
    { title: 'Contract Type', dataIndex: 'contract_type' },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: MarketData) =>
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

      <Table columns={columns} dataSource={data} rowKey="id" size="small" scroll={{ x: 1200 }} />

      <Modal
        title={editingData ? 'Edit Market Data' : 'Add Market Data'}
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
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="building_area" label="Building Area (m²)">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="floors" label="Floors">
              <InputNumber min={1} style={{ width: 100 }} />
            </Form.Item>
            <Form.Item name="structure" label="Structure">
              <Input style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="contract_value" label="Contract Value">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="prepayment_ratio" label="Prepayment %">
              <InputNumber min={0} max={100} precision={2} style={{ width: 100 }} />
            </Form.Item>
            <Form.Item name="advance_amount" label="Advance Amount">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="progress_payment_ratio" label="Progress Payment %">
              <InputNumber min={0} max={100} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="contract_type" label="Contract Type">
              <Input style={{ width: 200 }} />
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

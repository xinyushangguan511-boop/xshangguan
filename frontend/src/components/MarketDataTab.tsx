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
      message.success('数据创建成功');
      queryClient.invalidateQueries({ queryKey: ['marketData', projectId] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('数据创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MarketData> }) =>
      marketApi.update(projectId, id, data),
    onSuccess: () => {
      message.success('数据更新成功');
      queryClient.invalidateQueries({ queryKey: ['marketData', projectId] });
      setModalOpen(false);
      setEditingData(null);
      form.resetFields();
    },
    onError: () => message.error('数据更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => marketApi.delete(projectId, id),
    onSuccess: () => {
      message.success('数据删除成功');
      queryClient.invalidateQueries({ queryKey: ['marketData', projectId] });
    },
    onError: () => message.error('数据删除失败'),
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
    { title: '年份', dataIndex: 'year', width: 80 },
    { title: '月份', dataIndex: 'month', width: 80 },
    { title: '建筑面积 (m²)', dataIndex: 'building_area', render: (v: number) => formatNumber(v) },
    { title: '结构形式', dataIndex: 'structure' },
    { title: '层数', dataIndex: 'floors' },
    { title: '合同金额', dataIndex: 'contract_value', render: (v: number) => formatCurrency(v) },
    { title: '预付款比例', dataIndex: 'prepayment_ratio', render: (v: number) => v ? `${v}%` : '-' },
    { title: '合同类型', dataIndex: 'contract_type' },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: MarketData) =>
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
      {canEdit && (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          style={{ marginBottom: 16 }}
        >
          新增数据
        </Button>
      )}

      <Table columns={columns} dataSource={data} rowKey="id" size="small" scroll={{ x: 1200 }} />

      <Modal
        title={editingData ? '编辑市场数据' : '新增市场数据'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false);
          setEditingData(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={700}
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
            <Form.Item name="building_area" label="建筑面积 (m²)">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="floors" label="层数">
              <InputNumber min={1} style={{ width: 100 }} />
            </Form.Item>
            <Form.Item name="structure" label="结构形式">
              <Input style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="contract_value" label="合同金额">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="prepayment_ratio" label="预付款比例 %">
              <InputNumber min={0} max={100} precision={2} style={{ width: 100 }} />
            </Form.Item>
            <Form.Item name="advance_amount" label="预付款金额">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="progress_payment_ratio" label="进度款比例 %">
              <InputNumber min={0} max={100} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="contract_type" label="合同类型">
              <Input style={{ width: 200 }} />
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

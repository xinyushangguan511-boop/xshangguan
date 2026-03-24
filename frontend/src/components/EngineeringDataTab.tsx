import React, { useState } from 'react';
import { Table, Button, Modal, Form, InputNumber, Input, Select, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { engineeringApi } from '../services/api';
import { ExcelImportModal } from './ExcelImportModal';
import { ModuleAttachmentsModal } from './ModuleAttachmentsModal';
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
      message.success('数据创建成功');
      queryClient.invalidateQueries({ queryKey: ['engineeringData', projectId] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('数据创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EngineeringData> }) =>
      engineeringApi.update(projectId, id, data),
    onSuccess: () => {
      message.success('数据更新成功');
      queryClient.invalidateQueries({ queryKey: ['engineeringData', projectId] });
      setModalOpen(false);
      setEditingData(null);
      form.resetFields();
    },
    onError: () => message.error('数据更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => engineeringApi.delete(projectId, id),
    onSuccess: () => {
      message.success('数据删除成功');
      queryClient.invalidateQueries({ queryKey: ['engineeringData', projectId] });
    },
    onError: () => message.error('数据删除失败'),
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
    { title: '年份', dataIndex: 'year', width: 80 },
    { title: '月份', dataIndex: 'month', width: 80 },
    { title: '实际工期', dataIndex: 'actual_duration', render: (v: number) => v ? `${v}天` : '-' },
    { title: '期末进度', dataIndex: 'end_period_progress', ellipsis: true },
    { title: '合同金额', dataIndex: 'contract_value', render: (v: number) => formatCurrency(v) },
    { title: '月产值', dataIndex: 'monthly_output', render: (v: number) => formatCurrency(v) },
    { title: '计划产值', dataIndex: 'planned_output', render: (v: number) => formatCurrency(v) },
    { title: '月批复', dataIndex: 'monthly_approval', render: (v: number) => formatCurrency(v) },
    { title: '管理人员', dataIndex: 'staff_count', render: (v: number) => formatNumber(v, 0) },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: EngineeringData) =>
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
      <Space wrap style={{ marginBottom: 16 }}>
        {canEdit && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            新增数据
          </Button>
        )}
        {canEdit && <ExcelImportModal dataType="engineering" projectId={projectId} />}
        <ModuleAttachmentsModal projectId={projectId} module="engineering" />
      </Space>

      <Table columns={columns} dataSource={data} rowKey="id" size="small" scroll={{ x: 1400 }} />

      <Modal
        title={editingData ? '编辑工程数据' : '新增工程数据'}
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
            <Form.Item name="actual_duration" label="实际工期（天）">
              <InputNumber min={0} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          <Form.Item name="end_period_progress" label="期末进度">
            <Input />
          </Form.Item>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="contract_value" label="合同金额">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="monthly_output" label="月产值">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="planned_output" label="计划产值">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Space style={{ display: 'flex' }}>
            <Form.Item name="monthly_approval" label="月批复">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="staff_count" label="管理人员">
              <InputNumber min={0} style={{ width: 100 }} />
            </Form.Item>
            <Form.Item name="next_month_plan" label="下月计划">
              <InputNumber min={0} precision={2} style={{ width: 150 }} />
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

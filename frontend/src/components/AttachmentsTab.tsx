import React, { useState } from 'react';
import { Table, Button, Upload, Modal, Select, Space, message, Popconfirm, Tag } from 'antd';
import { UploadOutlined, DownloadOutlined, DeleteOutlined, InboxOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { attachmentsApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatFileSize, getDepartmentColor, getDepartmentText } from '../utils';
import type { Attachment } from '../types';

const { Dragger } = Upload;

interface Props {
  projectId: string;
  data: Attachment[];
}

const FILE_TYPES = [
  { value: 'contract', label: '合同' },
  { value: 'certificate', label: '证书' },
  { value: 'report', label: '报告' },
  { value: 'drawing', label: '图纸' },
  { value: 'photo', label: '照片' },
  { value: 'other', label: '其他' },
];

export const AttachmentsTab: React.FC<Props> = ({ projectId, data }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [fileType, setFileType] = useState<string>('other');
  const [fileList, setFileList] = useState<File[]>([]);
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: ({ file, fileType }: { file: File; fileType: string }) =>
      attachmentsApi.upload(projectId, file, fileType),
    onSuccess: () => {
      message.success('文件上传成功');
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId] });
      setModalOpen(false);
      setFileList([]);
    },
    onError: () => message.error('文件上传失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => attachmentsApi.delete(id),
    onSuccess: () => {
      message.success('文件删除成功');
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId] });
    },
    onError: () => message.error('文件删除失败'),
  });

  const handleDownload = async (attachment: Attachment) => {
    try {
      const blob = await attachmentsApi.download(attachment.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachment.file_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      message.error('文件下载失败');
    }
  };

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.warning('请选择要上传的文件');
      return;
    }
    uploadMutation.mutate({ file: fileList[0], fileType });
  };

  const columns = [
    { title: '文件名', dataIndex: 'file_name', ellipsis: true },
    {
      title: '类型',
      dataIndex: 'file_type',
      width: 100,
      render: (type: string) => FILE_TYPES.find(t => t.value === type)?.label || type || '-',
    },
    {
      title: '所属部门',
      dataIndex: 'department',
      width: 120,
      render: (dept: string) => (
        <Tag color={getDepartmentColor(dept as any)}>{getDepartmentText(dept as any)}</Tag>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: Attachment) => (
        <Space>
          <Button type="link" icon={<DownloadOutlined />} onClick={() => handleDownload(record)} />
          {(record.uploaded_by === user?.id || user?.department === 'admin') && (
            <Popconfirm title="确定删除该文件？" onConfirm={() => deleteMutation.mutate(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Button
        type="primary"
        icon={<UploadOutlined />}
        onClick={() => setModalOpen(true)}
        style={{ marginBottom: 16 }}
      >
        上传文件
      </Button>

      <Table columns={columns} dataSource={data} rowKey="id" size="small" />

      <Modal
        title="上传文件"
        open={modalOpen}
        onOk={handleUpload}
        onCancel={() => {
          setModalOpen(false);
          setFileList([]);
        }}
        confirmLoading={uploadMutation.isPending}
        okText="确定"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            value={fileType}
            onChange={setFileType}
            style={{ width: '100%' }}
            placeholder="选择文件类型"
          >
            {FILE_TYPES.map(t => (
              <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
            ))}
          </Select>

          <Dragger
            beforeUpload={(file) => {
              setFileList([file]);
              return false;
            }}
            fileList={fileList.map(f => ({ uid: f.name, name: f.name, status: 'done' as const }))}
            onRemove={() => setFileList([])}
            maxCount={1}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持格式：PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, ZIP（最大50MB）
            </p>
          </Dragger>
        </Space>
      </Modal>
    </div>
  );
};

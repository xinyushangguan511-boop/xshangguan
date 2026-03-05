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
  { value: 'contract', label: 'Contract' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'report', label: 'Report' },
  { value: 'drawing', label: 'Drawing' },
  { value: 'photo', label: 'Photo' },
  { value: 'other', label: 'Other' },
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
      message.success('File uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId] });
      setModalOpen(false);
      setFileList([]);
    },
    onError: () => message.error('Failed to upload file'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => attachmentsApi.delete(id),
    onSuccess: () => {
      message.success('File deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId] });
    },
    onError: () => message.error('Failed to delete file'),
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
      message.error('Failed to download file');
    }
  };

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.warning('Please select a file');
      return;
    }
    uploadMutation.mutate({ file: fileList[0], fileType });
  };

  const columns = [
    { title: 'File Name', dataIndex: 'file_name', ellipsis: true },
    {
      title: 'Type',
      dataIndex: 'file_type',
      width: 100,
      render: (type: string) => FILE_TYPES.find(t => t.value === type)?.label || type || '-',
    },
    {
      title: 'Department',
      dataIndex: 'department',
      width: 120,
      render: (dept: string) => (
        <Tag color={getDepartmentColor(dept as any)}>{getDepartmentText(dept as any)}</Tag>
      ),
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: 'Uploaded At',
      dataIndex: 'uploaded_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: Attachment) => (
        <Space>
          <Button type="link" icon={<DownloadOutlined />} onClick={() => handleDownload(record)} />
          {(record.uploaded_by === user?.id || user?.department === 'admin') && (
            <Popconfirm title="Delete this file?" onConfirm={() => deleteMutation.mutate(record.id)}>
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
        Upload File
      </Button>

      <Table columns={columns} dataSource={data} rowKey="id" size="small" />

      <Modal
        title="Upload File"
        open={modalOpen}
        onOk={handleUpload}
        onCancel={() => {
          setModalOpen(false);
          setFileList([]);
        }}
        confirmLoading={uploadMutation.isPending}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            value={fileType}
            onChange={setFileType}
            style={{ width: '100%' }}
            placeholder="Select file type"
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
            <p className="ant-upload-text">Click or drag file to upload</p>
            <p className="ant-upload-hint">
              Supported: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, ZIP (max 50MB)
            </p>
          </Dragger>
        </Space>
      </Modal>
    </div>
  );
};

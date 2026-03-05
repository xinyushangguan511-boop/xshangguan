import React, { useState } from 'react';
import { Table, Select, Card, Button, Typography, Space, Spin, Tag, message, Popconfirm } from 'antd';
import { DownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { projectsApi, attachmentsApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatFileSize, getDepartmentColor, getDepartmentText } from '../utils';
import type { Attachment } from '../types';

const { Title } = Typography;

export const AttachmentsPage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | undefined>();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: attachments, isLoading: attachmentsLoading } = useQuery({
    queryKey: ['attachments', selectedProject],
    queryFn: () => attachmentsApi.list(selectedProject!),
    enabled: !!selectedProject,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => attachmentsApi.delete(id),
    onSuccess: () => {
      message.success('File deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['attachments', selectedProject] });
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

  const columns = [
    { title: 'File Name', dataIndex: 'file_name', ellipsis: true },
    { title: 'Type', dataIndex: 'file_type', width: 100 },
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
      <Title level={4}>File Center</Title>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>Select Project:</span>
          <Select
            style={{ width: 400 }}
            placeholder="Select a project"
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
          {attachmentsLoading ? (
            <div style={{ textAlign: 'center', padding: 50 }}>
              <Spin />
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={attachments}
              rowKey="id"
              size="small"
            />
          )}
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>
            Please select a project to view attachments
          </div>
        </Card>
      )}
    </div>
  );
};

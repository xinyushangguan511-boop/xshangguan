import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Table, Select, Card, Button, Typography, Space, Spin, Tag, message, Popconfirm } from 'antd';
import { DownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { projectsApi, attachmentsApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import { formatFileSize, getAttachmentModuleText, getDepartmentColor, getDepartmentText } from '../utils';
import type { Attachment, AttachmentModule } from '../types';

const { Title } = Typography;

export const AttachmentsPage: React.FC = () => {
  const { id: routeProjectId } = useParams<{ id: string }>();
  // 如果是从“项目附件”按钮跳进来，默认带上当前项目；从菜单进入则保持为空。
  const [selectedProject, setSelectedProject] = useState<string | undefined>(routeProjectId);
  const [selectedModule, setSelectedModule] = useState<AttachmentModule | undefined>();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: attachments, isLoading: attachmentsLoading } = useQuery({
    queryKey: ['attachments', selectedProject, selectedModule],
    // 附件中心支持按模块查看，方便把项目附件和业务板块附件分开排查。
    queryFn: () => attachmentsApi.list(selectedProject!, selectedModule),
    enabled: !!selectedProject,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => attachmentsApi.delete(id),
    onSuccess: () => {
      message.success('文件删除成功');
      queryClient.invalidateQueries({ queryKey: ['attachments', selectedProject] });
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

  const columns = [
    { title: '文件名', dataIndex: 'file_name', ellipsis: true },
    { title: '类型', dataIndex: 'file_type', width: 100 },
    {
      title: '板块',
      dataIndex: 'module',
      width: 100,
      render: (module: AttachmentModule) => getAttachmentModuleText(module),
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
      <Title level={4}>附件中心</Title>

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
          <span>板块筛选：</span>
          <Select
            style={{ width: 160 }}
            placeholder="全部板块"
            allowClear
            value={selectedModule}
            onChange={setSelectedModule}
          >
            <Select.Option value="project">项目</Select.Option>
            <Select.Option value="market">市场</Select.Option>
            <Select.Option value="engineering">工程</Select.Option>
            <Select.Option value="finance">财务</Select.Option>
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
            请选择项目查看附件
          </div>
        </Card>
      )}
    </div>
  );
};

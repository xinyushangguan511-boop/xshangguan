import React, { useState } from 'react';
import { Button, Modal, Popconfirm, Select, Space, Table, Tag, Upload, message } from 'antd';
import { DeleteOutlined, DownloadOutlined, InboxOutlined, PaperClipOutlined, UploadOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { attachmentsApi } from '../services/api';
import { useAuth } from '../stores/AuthContext';
import {
  formatFileSize,
  getAttachmentModuleText,
  getDepartmentColor,
  getDepartmentText,
} from '../utils';
import type { Attachment, AttachmentModule } from '../types';

const { Dragger } = Upload;

interface Props {
  projectId: string;
  module: Exclude<AttachmentModule, 'project'>;
  buttonText?: string;
}

const FILE_TYPES = [
  { value: 'contract', label: '合同' },
  { value: 'certificate', label: '证书' },
  { value: 'report', label: '报告' },
  { value: 'drawing', label: '图纸' },
  { value: 'photo', label: '照片' },
  { value: 'other', label: '其他' },
];

export const ModuleAttachmentsModal: React.FC<Props> = ({ projectId, module, buttonText }) => {
  const [open, setOpen] = useState(false);
  const [fileList, setFileList] = useState<File[]>([]);
  const [fileType, setFileType] = useState<string>('other');
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // 这里沿用现有权限模型：管理员可上传，业务部门只能上传自己板块的附件。
  const canUpload = user?.department === 'admin' || user?.department === module;

  const { data, isLoading } = useQuery({
    queryKey: ['attachments', projectId, module],
    queryFn: () => attachmentsApi.list(projectId, module),
    // 只有打开弹窗时才查询，避免页面初次渲染时把所有板块附件都请求一遍。
    enabled: open,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, selectedFileType }: { file: File; selectedFileType: string }) =>
      attachmentsApi.uploadByModule(projectId, module, file, selectedFileType),
    onSuccess: () => {
      message.success('附件上传成功');
      // 同时刷新“模块附件列表”和“项目附件总列表”，保持两个视图一致。
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId, module] });
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId] });
      setFileList([]);
    },
    onError: () => {
      message.error('附件上传失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (attachmentId: string) => attachmentsApi.delete(attachmentId),
    onSuccess: () => {
      message.success('附件删除成功');
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId, module] });
      queryClient.invalidateQueries({ queryKey: ['attachments', projectId] });
    },
    onError: () => {
      message.error('附件删除失败');
    },
  });

  const handleDownload = async (attachment: Attachment) => {
    try {
      const blob = await attachmentsApi.download(attachment.id);
      // 后端返回二进制流，这里手动创建 a 标签完成浏览器下载。
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = attachment.file_name;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch {
      message.error('附件下载失败');
    }
  };

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.warning('请选择要上传的文件');
      return;
    }

    uploadMutation.mutate({ file: fileList[0], selectedFileType: fileType });
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      width: 100,
      render: (value: string) => FILE_TYPES.find((item) => item.value === value)?.label || value || '-',
    },
    {
      title: '部门',
      dataIndex: 'department',
      width: 100,
      render: (department: Attachment['department']) => (
        <Tag color={getDepartmentColor(department)}>{getDepartmentText(department)}</Tag>
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
      width: 160,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: Attachment) => (
        <Space>
          <Button type="link" icon={<DownloadOutlined />} onClick={() => handleDownload(record)} />
          {(record.uploaded_by === user?.id || user?.department === 'admin') && (
            <Popconfirm title="确定删除该附件？" onConfirm={() => deleteMutation.mutate(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <>
      <Button icon={<PaperClipOutlined />} onClick={() => setOpen(true)}>
        {buttonText || `${getAttachmentModuleText(module)}附件`}
      </Button>

      <Modal
        title={`${getAttachmentModuleText(module)}附件管理`}
        open={open}
        onCancel={() => {
          setOpen(false);
          setFileList([]);
        }}
        footer={null}
        width={900}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {canUpload && (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space wrap>
                <Select value={fileType} onChange={setFileType} style={{ width: 180 }}>
                  {FILE_TYPES.map((item) => (
                    <Select.Option key={item.value} value={item.value}>
                      {item.label}
                    </Select.Option>
                  ))}
                </Select>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={handleUpload}
                  loading={uploadMutation.isPending}
                >
                  上传附件
                </Button>
              </Space>

              <Dragger
                beforeUpload={(file) => {
                  // 仅暂存文件，不让 antd 组件自己发请求，统一交给 mutation 处理。
                  setFileList([file]);
                  return false;
                }}
                fileList={fileList.map((file) => ({
                  uid: file.name,
                  name: file.name,
                  status: 'done' as const,
                }))}
                onRemove={() => setFileList([])}
                maxCount={1}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持 PDF、Office、图片、压缩包等常见格式
                </p>
              </Dragger>
            </Space>
          )}

          <Table
            columns={columns}
            dataSource={data || []}
            rowKey="id"
            loading={isLoading}
            size="small"
            pagination={{ pageSize: 5 }}
          />
        </Space>
      </Modal>
    </>
  );
};
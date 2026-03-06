import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Tabs, Descriptions, Tag, Button, Spin, Typography, Space } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { projectsApi, marketApi, engineeringApi, financeApi, attachmentsApi } from '../services/api';
import { getStatusColor, getStatusText } from '../utils';
import { MarketDataTab } from '../components/MarketDataTab';
import { EngineeringDataTab } from '../components/EngineeringDataTab';
import { FinanceDataTab } from '../components/FinanceDataTab';
import { AttachmentsTab } from '../components/AttachmentsTab';

const { Title } = Typography;

export const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id!),
    enabled: !!id,
  });

  const { data: marketData } = useQuery({
    queryKey: ['marketData', id],
    queryFn: () => marketApi.list(id!),
    enabled: !!id,
  });

  const { data: engineeringData } = useQuery({
    queryKey: ['engineeringData', id],
    queryFn: () => engineeringApi.list(id!),
    enabled: !!id,
  });

  const { data: financeData } = useQuery({
    queryKey: ['financeData', id],
    queryFn: () => financeApi.list(id!),
    enabled: !!id,
  });

  const { data: attachments } = useQuery({
    queryKey: ['attachments', id],
    queryFn: () => attachmentsApi.list(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!project) {
    return <div>项目未找到</div>;
  }

  const tabItems = [
    {
      key: 'info',
      label: '项目信息',
      children: (
        <Descriptions bordered column={2}>
          <Descriptions.Item label="项目编号">{project.project_code}</Descriptions.Item>
          <Descriptions.Item label="项目名称">{project.project_name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={getStatusColor(project.status)}>{getStatusText(project.status)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="施工单位">{project.construction_unit || '-'}</Descriptions.Item>
          <Descriptions.Item label="项目地址">{project.location || '-'}</Descriptions.Item>
          <Descriptions.Item label="合同工期">
            {project.contract_duration ? `${project.contract_duration}天` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="合同开始日期">
            {project.contract_start_date ? dayjs(project.contract_start_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="合同结束日期">
            {project.contract_end_date ? dayjs(project.contract_end_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="实际开始日期">
            {project.actual_start_date ? dayjs(project.actual_start_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(project.created_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="项目描述" span={2}>
            {project.description || '-'}
          </Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'market',
      label: `市场数据 (${marketData?.length || 0})`,
      children: <MarketDataTab projectId={id!} data={marketData || []} />,
    },
    {
      key: 'engineering',
      label: `工程数据 (${engineeringData?.length || 0})`,
      children: <EngineeringDataTab projectId={id!} data={engineeringData || []} />,
    },
    {
      key: 'finance',
      label: `财务数据 (${financeData?.length || 0})`,
      children: <FinanceDataTab projectId={id!} data={financeData || []} />,
    },
    {
      key: 'attachments',
      label: `附件 (${attachments?.length || 0})`,
      children: <AttachmentsTab projectId={id!} data={attachments || []} />,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>
          返回
        </Button>
        <Title level={4} style={{ margin: 0 }}>
          {project.project_name}
        </Title>
      </Space>

      <Card>
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
};

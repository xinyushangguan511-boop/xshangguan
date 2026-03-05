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
    return <div>Project not found</div>;
  }

  const tabItems = [
    {
      key: 'info',
      label: 'Project Info',
      children: (
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Project Code">{project.project_code}</Descriptions.Item>
          <Descriptions.Item label="Project Name">{project.project_name}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={getStatusColor(project.status)}>{getStatusText(project.status)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Construction Unit">{project.construction_unit || '-'}</Descriptions.Item>
          <Descriptions.Item label="Location">{project.location || '-'}</Descriptions.Item>
          <Descriptions.Item label="Contract Duration">
            {project.contract_duration ? `${project.contract_duration} days` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Contract Start">
            {project.contract_start_date ? dayjs(project.contract_start_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Contract End">
            {project.contract_end_date ? dayjs(project.contract_end_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Actual Start">
            {project.actual_start_date ? dayjs(project.actual_start_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Created At">
            {dayjs(project.created_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            {project.description || '-'}
          </Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'market',
      label: `Market Data (${marketData?.length || 0})`,
      children: <MarketDataTab projectId={id!} data={marketData || []} />,
    },
    {
      key: 'engineering',
      label: `Engineering Data (${engineeringData?.length || 0})`,
      children: <EngineeringDataTab projectId={id!} data={engineeringData || []} />,
    },
    {
      key: 'finance',
      label: `Finance Data (${financeData?.length || 0})`,
      children: <FinanceDataTab projectId={id!} data={financeData || []} />,
    },
    {
      key: 'attachments',
      label: `Attachments (${attachments?.length || 0})`,
      children: <AttachmentsTab projectId={id!} data={attachments || []} />,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>
          Back
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

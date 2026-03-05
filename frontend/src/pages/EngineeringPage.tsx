import React, { useState } from 'react';
import { Table, Select, Card, Typography, Space, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { projectsApi, engineeringApi } from '../services/api';
import { formatCurrency, formatNumber } from '../utils';
import type { EngineeringData } from '../types';

const { Title } = Typography;

export const EngineeringPage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | undefined>();

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: engineeringData, isLoading: dataLoading } = useQuery({
    queryKey: ['engineeringData', selectedProject],
    queryFn: () => engineeringApi.list(selectedProject!),
    enabled: !!selectedProject,
  });

  const columns = [
    { title: 'Year', dataIndex: 'year', width: 80 },
    { title: 'Month', dataIndex: 'month', width: 80 },
    { title: 'Actual Duration', dataIndex: 'actual_duration', render: (v: number) => v ? `${v} days` : '-' },
    { title: 'Progress', dataIndex: 'end_period_progress', ellipsis: true },
    { title: 'Contract Value', dataIndex: 'contract_value', render: (v: number) => formatCurrency(v) },
    { title: 'Monthly Output', dataIndex: 'monthly_output', render: (v: number) => formatCurrency(v) },
    { title: 'Planned Output', dataIndex: 'planned_output', render: (v: number) => formatCurrency(v) },
    { title: 'Monthly Approval', dataIndex: 'monthly_approval', render: (v: number) => formatCurrency(v) },
    { title: 'Staff', dataIndex: 'staff_count', render: (v: number) => formatNumber(v, 0) },
    { title: 'Next Month Plan', dataIndex: 'next_month_plan', render: (v: number) => formatCurrency(v) },
    { title: 'Remarks', dataIndex: 'remarks', ellipsis: true },
  ];

  return (
    <div>
      <Title level={4}>Engineering Data</Title>

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
          {dataLoading ? (
            <div style={{ textAlign: 'center', padding: 50 }}>
              <Spin />
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={engineeringData}
              rowKey="id"
              size="small"
              scroll={{ x: 1600 }}
            />
          )}
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>
            Please select a project to view engineering data
          </div>
        </Card>
      )}
    </div>
  );
};

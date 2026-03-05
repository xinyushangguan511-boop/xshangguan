import React, { useState } from 'react';
import { Table, Select, Card, Typography, Space, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { projectsApi, financeApi } from '../services/api';
import { formatCurrency } from '../utils';
import type { FinanceData } from '../types';

const { Title } = Typography;

export const FinancePage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | undefined>();

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: financeData, isLoading: dataLoading } = useQuery({
    queryKey: ['financeData', selectedProject],
    queryFn: () => financeApi.list(selectedProject!),
    enabled: !!selectedProject,
  });

  const columns = [
    { title: 'Year', dataIndex: 'year', width: 80 },
    { title: 'Month', dataIndex: 'month', width: 80 },
    { title: 'Monthly Revenue', dataIndex: 'monthly_revenue', render: (v: number) => formatCurrency(v) },
    { title: 'Monthly Cost', dataIndex: 'monthly_cost', render: (v: number) => formatCurrency(v) },
    { title: 'Payment Received', dataIndex: 'monthly_payment_received', render: (v: number) => formatCurrency(v) },
    { title: 'Target Margin %', dataIndex: 'target_margin', render: (v: number) => v ? `${v}%` : '-' },
    { title: 'Remarks', dataIndex: 'remarks', ellipsis: true },
  ];

  return (
    <div>
      <Title level={4}>Finance Data</Title>

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
              dataSource={financeData}
              rowKey="id"
              size="small"
              scroll={{ x: 1000 }}
            />
          )}
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>
            Please select a project to view finance data
          </div>
        </Card>
      )}
    </div>
  );
};

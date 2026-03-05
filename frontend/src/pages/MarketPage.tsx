import React, { useState } from 'react';
import { Table, Select, Card, Typography, Space, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { projectsApi, marketApi } from '../services/api';
import { formatCurrency, formatNumber } from '../utils';
import type { MarketData } from '../types';

const { Title } = Typography;

export const MarketPage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | undefined>();

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: marketData, isLoading: dataLoading } = useQuery({
    queryKey: ['marketData', selectedProject],
    queryFn: () => marketApi.list(selectedProject!),
    enabled: !!selectedProject,
  });

  const columns = [
    { title: 'Year', dataIndex: 'year', width: 80 },
    { title: 'Month', dataIndex: 'month', width: 80 },
    { title: 'Building Area (m²)', dataIndex: 'building_area', render: (v: number) => formatNumber(v) },
    { title: 'Structure', dataIndex: 'structure' },
    { title: 'Floors', dataIndex: 'floors' },
    { title: 'Contract Value', dataIndex: 'contract_value', render: (v: number) => formatCurrency(v) },
    { title: 'Prepayment %', dataIndex: 'prepayment_ratio', render: (v: number) => v ? `${v}%` : '-' },
    { title: 'Advance Amount', dataIndex: 'advance_amount', render: (v: number) => formatCurrency(v) },
    { title: 'Progress Payment %', dataIndex: 'progress_payment_ratio', render: (v: number) => v ? `${v}%` : '-' },
    { title: 'Contract Type', dataIndex: 'contract_type' },
    { title: 'Remarks', dataIndex: 'remarks', ellipsis: true },
  ];

  return (
    <div>
      <Title level={4}>Market Data</Title>

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
              dataSource={marketData}
              rowKey="id"
              size="small"
              scroll={{ x: 1400 }}
            />
          )}
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>
            Please select a project to view market data
          </div>
        </Card>
      )}
    </div>
  );
};

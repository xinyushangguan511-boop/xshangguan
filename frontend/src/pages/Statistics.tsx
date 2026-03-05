import React, { useState } from 'react';
import { Card, Row, Col, Select, Tabs, Statistic, Typography, Space, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import ReactECharts from 'echarts-for-react';
import { projectsApi, statisticsApi } from '../services/api';
import { formatCurrency } from '../utils';

const { Title } = Typography;

export const Statistics: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | undefined>();

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 100),
  });

  const { data: marketSummary, isLoading: marketLoading } = useQuery({
    queryKey: ['marketSummary', selectedProject],
    queryFn: () => statisticsApi.marketSummary(selectedProject),
  });

  const { data: engineeringSummary, isLoading: engineeringLoading } = useQuery({
    queryKey: ['engineeringSummary', selectedProject],
    queryFn: () => statisticsApi.engineeringSummary(selectedProject),
  });

  const { data: financeSummary, isLoading: financeLoading } = useQuery({
    queryKey: ['financeSummary', selectedProject],
    queryFn: () => statisticsApi.financeSummary(selectedProject),
  });

  const isLoading = marketLoading || engineeringLoading || financeLoading;

  const marketChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Monthly', 'Quarterly'] },
    xAxis: {
      type: 'category',
      data: marketSummary?.contract_value_monthly.map(d => `${d.year}-${d.month}`) || [],
    },
    yAxis: { type: 'value', name: 'Contract Value' },
    series: [
      {
        name: 'Monthly',
        data: marketSummary?.contract_value_monthly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#722ed1' },
      },
    ],
  };

  const engineeringChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Output', 'Approval'] },
    xAxis: {
      type: 'category',
      data: engineeringSummary?.monthly_output_cumulative.map(d => `${d.year}-${d.month}`) || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'Output',
        data: engineeringSummary?.monthly_output_cumulative.map(d => d.total) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#13c2c2' },
      },
      {
        name: 'Approval',
        data: engineeringSummary?.monthly_approval_cumulative.map(d => d.total) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#fa8c16' },
      },
    ],
  };

  const financeChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Revenue', 'Cost', 'Payment'] },
    xAxis: {
      type: 'category',
      data: financeSummary?.revenue_quarterly.map(d => `${d.year} Q${d.quarter}`) || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'Revenue',
        data: financeSummary?.revenue_quarterly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#52c41a' },
      },
      {
        name: 'Cost',
        data: financeSummary?.cost_quarterly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#ff4d4f' },
      },
      {
        name: 'Payment',
        data: financeSummary?.payment_quarterly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#1890ff' },
      },
    ],
  };

  const tabItems = [
    {
      key: 'market',
      label: 'Market Statistics',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Total Contract Value"
                  value={marketSummary?.total_contract_value || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
          </Row>
          <Card title="Contract Value Trend">
            <ReactECharts option={marketChartOption} style={{ height: 400 }} />
          </Card>
        </div>
      ),
    },
    {
      key: 'engineering',
      label: 'Engineering Statistics',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Output"
                  value={engineeringSummary?.total_output || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Approval"
                  value={engineeringSummary?.total_approval || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Approval Rate"
                  value={engineeringSummary?.approval_rate || 0}
                  precision={2}
                  suffix="%"
                />
              </Card>
            </Col>
          </Row>
          <Card title="Output & Approval Trend">
            <ReactECharts option={engineeringChartOption} style={{ height: 400 }} />
          </Card>
        </div>
      ),
    },
    {
      key: 'finance',
      label: 'Finance Statistics',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Revenue"
                  value={financeSummary?.total_revenue || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Cost"
                  value={financeSummary?.total_cost || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Payment"
                  value={financeSummary?.total_payment || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Gross Margin"
                  value={financeSummary?.gross_margin || 0}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: (financeSummary?.gross_margin || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>
          <Card title="Quarterly Financial Trend">
            <ReactECharts option={financeChartOption} style={{ height: 400 }} />
          </Card>
        </div>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>Statistics & Reports</Title>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>Filter by Project:</span>
          <Select
            style={{ width: 400 }}
            placeholder="All Projects"
            loading={projectsLoading}
            value={selectedProject}
            onChange={setSelectedProject}
            allowClear
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

      {isLoading ? (
        <Card>
          <div style={{ textAlign: 'center', padding: 100 }}>
            <Spin size="large" />
          </div>
        </Card>
      ) : (
        <Card>
          <Tabs items={tabItems} />
        </Card>
      )}
    </div>
  );
};

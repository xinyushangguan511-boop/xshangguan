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
    legend: { data: ['月度', '季度'] },
    xAxis: {
      type: 'category',
      data: marketSummary?.contract_value_monthly.map(d => `${d.year}-${d.month}`) || [],
    },
    yAxis: { type: 'value', name: '合同金额' },
    series: [
      {
        name: '月度',
        data: marketSummary?.contract_value_monthly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#722ed1' },
      },
    ],
  };

  const engineeringChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['产值', '甲供批复'] },
    xAxis: {
      type: 'category',
      data: engineeringSummary?.monthly_output_cumulative.map(d => `${d.year}-${d.month}`) || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '产值',
        data: engineeringSummary?.monthly_output_cumulative.map(d => d.total) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#13c2c2' },
      },
      {
        name: '甲供批复',
        data: engineeringSummary?.monthly_approval_cumulative.map(d => d.total) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#fa8c16' },
      },
    ],
  };

  const financeChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['营收', '成本', '回款'] },
    xAxis: {
      type: 'category',
      data: financeSummary?.revenue_quarterly.map(d => `${d.year} 第${d.quarter}季度`) || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '营收',
        data: financeSummary?.revenue_quarterly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#52c41a' },
      },
      {
        name: '成本',
        data: financeSummary?.cost_quarterly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#ff4d4f' },
      },
      {
        name: '回款',
        data: financeSummary?.payment_quarterly.map(d => d.total) || [],
        type: 'bar',
        itemStyle: { color: '#1890ff' },
      },
    ],
  };

  const tabItems = [
    {
      key: 'market',
      label: '市场统计',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="合同总金额"
                  value={marketSummary?.total_contract_value || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
          </Row>
          <Card title="合同金额趋势">
            <ReactECharts option={marketChartOption} style={{ height: 400 }} />
          </Card>
        </div>
      ),
    },
    {
      key: 'engineering',
      label: '工程统计',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="累计产值"
                  value={engineeringSummary?.total_output || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="累计批复"
                  value={engineeringSummary?.total_approval || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="批复率"
                  value={engineeringSummary?.approval_rate || 0}
                  precision={2}
                  suffix="%"
                />
              </Card>
            </Col>
          </Row>
          <Card title="产值与批复趋势">
            <ReactECharts option={engineeringChartOption} style={{ height: 400 }} />
          </Card>
        </div>
      ),
    },
    {
      key: 'finance',
      label: '财务统计',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="累计营收"
                  value={financeSummary?.total_revenue || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="累计成本"
                  value={financeSummary?.total_cost || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="累计回款"
                  value={financeSummary?.total_payment || 0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="毛利率"
                  value={financeSummary?.gross_margin || 0}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: (financeSummary?.gross_margin || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>
          <Card title="季度财务趋势">
            <ReactECharts option={financeChartOption} style={{ height: 400 }} />
          </Card>
        </div>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>统计报表</Title>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>按项目筛选：</span>
          <Select
            style={{ width: 400 }}
            placeholder="全部项目"
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

/**
 * Analytics integration for Tracera
 * 
 * Traces to: FR-TRACERA-ANALYTICS-001
 * 
 * Product analytics for distributed tracing platform
 */

import { initAnalytics, track, identify, EventType } from '@phenotype/analytics';

const ANALYTICS_ENDPOINT = process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT || 'https://analytics.phenotype.dev/v1/events';
const ANALYTICS_KEY = process.env.NEXT_PUBLIC_ANALYTICS_KEY || '';

export function initTraceraAnalytics() {
  if (!ANALYTICS_KEY) return;

  initAnalytics({
    endpoint: ANALYTICS_ENDPOINT,
    apiKey: ANALYTICS_KEY,
    environment: process.env.NODE_ENV || 'development',
    version: process.env.TRACERA_VERSION,
    debug: process.env.NODE_ENV === 'development',
  });
}

// Trace collection events
export function traceReceived(
  traceId: string,
  serviceName: string,
  spanCount: number,
  sizeBytes: number
) {
  track(EventType.FEATURE_USED, {
    feature: 'trace_collection',
    trace_id: traceId,
    service_name: serviceName,
    span_count: spanCount,
    size_bytes: sizeBytes,
  });
}

// Dashboard interactions
export function trackDashboardView(viewType: string, filters: Record<string, unknown>) {
  track(EventType.PAGE_VIEW, {
    page: `dashboard/${viewType}`,
    filters: Object.keys(filters),
  });
}

export function trackTraceSearch(query: string, resultCount: number, durationMs: number) {
  track(EventType.FEATURE_USED, {
    feature: 'trace_search',
    query_length: query.length,
    result_count: resultCount,
    duration_ms: durationMs,
  });
}

// Alert events
export function trackAlertTriggered(
  alertId: string,
  serviceName: string,
  severity: string
) {
  track(EventType.WARNING_SHOWN, {
    alert_id: alertId,
    service_name: serviceName,
    severity,
    type: 'alert_triggered',
  });
}

export function trackAlertResolved(alertId: string, durationMinutes: number) {
  track(EventType.OPERATION_COMPLETED, {
    operation: 'alert_resolution',
    alert_id: alertId,
    duration_minutes: durationMinutes,
  });
}

// Service registration
export function trackServiceRegistered(serviceName: string, serviceType: string, userId: string) {
  identify(userId, {
    service_name: serviceName,
    service_type: serviceType,
    registered_at: new Date().toISOString(),
  });
  
  track(EventType.FEATURE_USED, {
    feature: 'service_registration',
    service_name: serviceName,
    service_type: serviceType,
  });
}

// Performance metrics
export function trackIngestionMetrics(
  tracesPerSecond: number,
  avgLatencyMs: number,
  storageUtilization: number
) {
  track(EventType.FEATURE_USED, {
    feature: 'ingestion_metrics',
    traces_per_second: tracesPerSecond,
    avg_latency_ms: avgLatencyMs,
    storage_utilization: storageUtilization,
  });
}

/**
 * Sentry configuration for Tracera
 * 
 * Traces to: FR-TRACERA-SENTRY-001
 * 
 * Error tracking for distributed tracing platform
 */

import { init } from '@sentry/nextjs';
import { BrowserTracing } from '@sentry/tracing';

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (SENTRY_DSN) {
  init({
    dsn: SENTRY_DSN,
    environment: process.env.SENTRY_ENVIRONMENT || process.env.NODE_ENV || 'development',
    release: process.env.TRACERA_RELEASE || process.env.VERCEL_GIT_COMMIT_SHA,
    
    integrations: [
      new BrowserTracing(),
    ],
    
    // High trace sampling for observability platform
    tracesSampleRate: 0.3,
    
    // Before send to avoid recursive error tracking
    beforeSend(event) {
      // Don't track errors from the tracing instrumentation itself
      if (event.exception?.values?.some(e => 
        e.stacktrace?.frames?.some(f => 
          f.filename?.includes('tracera-instrumentation')
        )
      )) {
        return null;
      }
      return event;
    },
  });
}

export const captureTraceError = (error: Error, traceId: string, spanId?: string) => {
  if (typeof window !== 'undefined' && (window as any).Sentry) {
    (window as any).Sentry.withScope((scope: any) => {
      scope.setTag('trace.id', traceId);
      if (spanId) {
        scope.setTag('span.id', spanId);
      }
      scope.setLevel('error');
      (window as any).Sentry.captureException(error);
    });
  }
};

export const setTraceContext = (traceId: string, serviceName: string) => {
  if (typeof window !== 'undefined' && (window as any).Sentry) {
    (window as any).Sentry.configureScope((scope: any) => {
      scope.setTag('trace.id', traceId);
      scope.setTag('service.name', serviceName);
    });
  }
};

export { SENTRY_DSN };

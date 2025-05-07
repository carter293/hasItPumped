'use client';

import {
  QueryClient,
  QueryClientProvider,
  HydrationBoundary,   // ← new name in v5
} from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export default function QueryProvider({
  children,
  dehydratedState = null,
}: {
  children: React.ReactNode;
  dehydratedState?: unknown;
}) {
  const [client] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={client}>
      <HydrationBoundary state={dehydratedState}>
        {children}
      </HydrationBoundary>

      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
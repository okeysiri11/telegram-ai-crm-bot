import { useEffect, useState } from 'react';
import { realtimeClient, type RealtimeStatus } from '../services/realtime';
import { useNotificationStore } from '../stores/notificationStore';
import type { RealtimeMessage } from '../types/api';

export function useRealtime(enabled = true): RealtimeStatus {
  const [status, setStatus] = useState<RealtimeStatus>('disconnected');
  const addNotification = useNotificationStore((s) => s.addFromRealtime);

  useEffect(() => {
    if (!enabled) return;

    const unsubStatus = realtimeClient.onStatus(setStatus);
    const unsubMsg = realtimeClient.onMessage((msg: RealtimeMessage) => {
      addNotification(msg);
    });

    realtimeClient.connect();

    return () => {
      unsubStatus();
      unsubMsg();
      realtimeClient.disconnect();
    };
  }, [enabled, addNotification]);

  return status;
}

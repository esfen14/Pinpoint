import { apiGet, apiPut } from './api'
import type { NotificationPolicy } from '../types/notificationPolicy'

export function getNotificationPolicy() {
  return apiGet<NotificationPolicy>('/api/system/notification-policy')
}

export function saveNotificationPolicy(policy: NotificationPolicy) {
  return apiPut<NotificationPolicy>('/api/system/notification-policy', policy)
}

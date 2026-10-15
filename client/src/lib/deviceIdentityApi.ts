import { apiGet, apiPost } from './api'
import type { AddressEvidence, DeviceSummary, IdentityEvidence, IdentityReview, MergeResult } from '../types/deviceIdentity'

export const getIdentityReviews = () => apiGet<{ items: IdentityReview[] }>('/api/system/discover/review')
export const getIdentityEvidence = (id: number) => apiGet<IdentityEvidence>(`/api/system/hosts/${id}/identifiers`)
export const getAddressEvidence = (id: number) => apiGet<AddressEvidence>(`/api/system/hosts/${id}/addresses`)
export const lookupIdentityDevices = (search: string) => apiGet<{ items: DeviceSummary[]; has_more: boolean }>(`/api/system/hosts/lookup?${new URLSearchParams({ search })}`)
export const mergeIdentityDevices = (source: number, target: number) => apiPost<MergeResult>(`/api/system/hosts/${source}/merge`, { target_id: target })

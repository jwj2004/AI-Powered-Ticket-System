import { USE_MOCK, request } from './http'

/**
 * GET /api/lookup?code=XXX
 * 结构化直查（保留自工单副驾）
 */
export async function lookupErrorCode(code) {
  if (USE_MOCK) {
    if (!code) {
      return {
        code: 'NOT_EXIST',
        name: '',
        meaning: '',
        trigger_condition: '',
        causes: [],
        solution: '',
        related_versions: [],
      }
    }
    return {
      code,
      name: '支付回调超时',
      meaning: '买家已付款但商城订单长时间未变成已支付',
      trigger_condition: '买家付款后 5 分钟内未收到支付平台异步通知',
      causes: ['商户平台回调地址不通', '店铺升级后回调路径变更'],
      solution: '先在支付商户后台确认已付款，再核对回调地址是否一致。',
      related_versions: ['v4.1.0+'],
    }
  }
  return request(`/api/lookup?code=${encodeURIComponent(code)}`)
}

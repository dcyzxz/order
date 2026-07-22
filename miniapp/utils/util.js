/**
 * 格式化时间
 */
function formatTime(date) {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = padZero(d.getMonth() + 1)
  const day = padZero(d.getDate())
  const hour = padZero(d.getHours())
  const minute = padZero(d.getMinutes())
  return year + '-' + month + '-' + day + ' ' + hour + ':' + minute
}

function padZero(n) {
  return n < 10 ? '0' + n : '' + n
}

/**
 * 订单状态文本映射
 */
function getOrderStatusText(status) {
  const map = {
    pending: '待处理',
    confirmed: '已确认',
    preparing: '制作中',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[status] || status
}

/**
 * 菜品状态文本映射
 */
function getDishStatusText(status) {
  const map = {
    active: '在售',
    inactive: '已下架',
    pending_price: '待定价',
  }
  return map[status] || status
}

/**
 * 待定价状态文本映射
 */
function getPendingStatusText(status) {
  const map = {
    pending_price: '待定价',
    approved: '已通过',
    rejected: '已驳回',
  }
  return map[status] || status
}

/**
 * 获取价格显示
 */
function formatPrice(price) {
  if (price === null || price === undefined) return '待定价'
  return '¥' + parseFloat(price).toFixed(2)
}

module.exports = {
  formatTime,
  getOrderStatusText,
  getDishStatusText,
  getPendingStatusText,
  formatPrice,
}

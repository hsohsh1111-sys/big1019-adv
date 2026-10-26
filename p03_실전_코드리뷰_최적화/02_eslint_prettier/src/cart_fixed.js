// ✅ 수정본: ESLint 경고 0개, Prettier 포맷 적용
const TAX_RATE = 0.1;

const COUPONS = {
  WELCOME: (sum) => sum - 5000,
  VIP: (sum) => sum * 0.9,
  HALF: (sum) => sum * 0.5,
  FREE: () => 0,
};

export function total(items, coupon) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const applyCoupon = COUPONS[coupon] ?? ((sum) => sum);
  const discounted = Math.max(applyCoupon(subtotal), 0);
  return Math.round(discounted * (1 + TAX_RATE));
}

const cart = [
  { name: "키보드", price: 39000, qty: 1 },
  { name: "마우스", price: 19000, qty: 2 },
];
console.log("결제 금액:", total(cart, "WELCOME"), "원");

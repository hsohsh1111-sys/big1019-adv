// ❌ 문제가 많은 코드: ESLint와 Prettier를 실행해 보세요.
var TAX = 0.1
const unused = "never used"

function total(items,coupon){
    let sum=0
    for(var i=0;i<items.length;i++){ sum = sum+items[i].price*items[i].qty }
    if(coupon == "WELCOME"){ sum = sum - 5000 }
    else if(coupon == "VIP"){ sum = sum*0.9 }
    else if(coupon == "HALF"){ sum = sum*0.5 }
    else if(coupon == "FREE"){ sum = 0 }
    if(sum < 0){ sum = 0 }
    let result = Math.round(sum*(1+TAX))
    return result
}

let cart = [{name:'키보드',price:39000,qty:1},{name:"마우스",price:19000,qty:2}]
console.log("결제 금액:", total(cart,"WELCOME"), "원")
console.log("디스카운트 확인:", discont)

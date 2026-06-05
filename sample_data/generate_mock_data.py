"""
模拟餐饮订单数据生成器
生成美团 / 微信点单 / 饿了么风格的真实订单数据，用于演示分析系统。

特点：
- 包含自然的时间周期性（工作日/周末、午餐/晚餐高峰）
- 隐藏商品关联购买规律（用于 Apriori 挖掘）
- 不同类型的顾客（高频高消费 / 低频低消费等）
- 包含退款和优惠数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ========== 配置区 ==========
np.random.seed(42)
random.seed(42)

# 商品库：{品类: [(商品名, 单价), ...]}
MENU = {
    "热菜": [
        ("宫保鸡丁", 28), ("鱼香肉丝", 26), ("回锅肉", 30),
        ("糖醋里脊", 32), ("红烧肉", 35), ("麻婆豆腐", 18),
        ("酸辣土豆丝", 16), ("西红柿炒蛋", 18), ("干锅花菜", 22),
        ("水煮肉片", 38), ("辣子鸡", 32), ("蒜蓉西兰花", 20),
    ],
    "凉菜": [
        ("凉拌黄瓜", 12), ("皮蛋豆腐", 14), ("口水鸡", 22),
        ("蒜泥白肉", 24), ("凉皮", 10),
    ],
    "汤类": [
        ("紫菜蛋花汤", 10), ("西红柿鸡蛋汤", 10), ("酸辣汤", 14),
        ("排骨汤", 22), ("菌菇汤", 18),
    ],
    "主食": [
        ("米饭", 2), ("蛋炒饭", 12), ("牛肉面", 18),
        ("水饺", 16), ("炒河粉", 15),
    ],
    "饮品": [
        ("可乐", 6), ("雪碧", 6), ("冰红茶", 5),
        ("矿泉水", 3), ("王老吉", 8), ("酸梅汤", 8),
    ],
    "小吃": [
        ("春卷", 10), ("煎饺", 14), ("花生米", 8),
        ("炸鸡翅", 16), ("烤串(5串)", 20),
    ],
}

# 关联购买规则（用于 Apriori 挖掘）
# 买了 A 的顾客有 probability 的概率也买了 B
ASSOCIATION_RULES = [
    ("酸辣土豆丝", "可乐", 0.35),
    ("宫保鸡丁", "紫菜蛋花汤", 0.25),
    ("鱼香肉丝", "西红柿鸡蛋汤", 0.25),
    ("回锅肉", "冰红茶", 0.20),
    ("水煮肉片", "米饭", 0.40),
    ("炸鸡翅", "可乐", 0.30),
    ("水饺", "酸辣汤", 0.22),
    ("糖醋里脊", "雪碧", 0.18),
    ("凉皮", "冰红茶", 0.20),
    ("烤串(5串)", "酸梅汤", 0.28),
    ("红烧肉", "米饭", 0.35),
    ("麻婆豆腐", "米饭", 0.30),
    ("水煮肉片", "凉拌黄瓜", 0.15),
    ("宫保鸡丁", "蛋炒饭", 0.12),
    ("口水鸡", "王老吉", 0.18),
]

# 平台分布
PLATFORMS = {
    "美团外卖": 0.45,
    "微信小程序": 0.30,
    "饿了么": 0.25,
}

# ========== 商品索引 ==========
ALL_PRODUCTS = []
ALL_PRICES = {}
PRODUCT_CATEGORY = {}
for cat, items in MENU.items():
    for name, price in items:
        ALL_PRODUCTS.append(name)
        ALL_PRICES[name] = price
        PRODUCT_CATEGORY[name] = cat


def build_association_map():
    """构建关联购买映射表"""
    assoc = {}
    for a, b, prob in ASSOCIATION_RULES:
        if a not in assoc:
            assoc[a] = []
        assoc[a].append((b, prob))
    return assoc


ASSOC_MAP = build_association_map()


def pick_category():
    """按品类权重抽样"""
    weights = {
        "热菜": 0.45, "凉菜": 0.10, "汤类": 0.12,
        "主食": 0.18, "饮品": 0.10, "小吃": 0.05,
    }
    cats = list(weights.keys())
    w = [weights[c] for c in cats]
    return np.random.choice(cats, p=np.array(w) / sum(w))


def pick_products():
    """根据真实点单逻辑生成一单的商品组合"""
    # 主食 or 主菜至少一个
    main_item = np.random.choice(ALL_PRODUCTS)
    items = [main_item]

    n_extra = np.random.choice([0, 0, 1, 1, 1, 2, 2, 3], p=[0.1, 0.1, 0.2, 0.15, 0.15, 0.12, 0.10, 0.08])

    available_extras = [p for p in ALL_PRODUCTS if p != main_item]

    # 检查关联规则
    if main_item in ASSOC_MAP:
        for assoc_item, prob in ASSOC_MAP[main_item]:
            if np.random.random() < prob and assoc_item not in items:
                items.append(assoc_item)
                n_extra -= 1
                if n_extra <= 0:
                    break

    # 随机补满
    extras = np.random.choice(available_extras, size=max(0, n_extra), replace=False)
    items.extend(extras)

    return items


def hour_sampler(hour_weights=None):
    """按小时分布抽样"""
    if hour_weights is None:
        # 默认午餐 + 晚餐高峰
        hour_weights = {
            0: 0.005, 1: 0.002, 2: 0.001, 3: 0.001,
            4: 0.001, 5: 0.002, 6: 0.005, 7: 0.01,
            8: 0.02, 9: 0.03, 10: 0.06, 11: 0.12,
            12: 0.13, 13: 0.06, 14: 0.03, 15: 0.02,
            16: 0.03, 17: 0.08, 18: 0.14, 19: 0.12,
            20: 0.06, 21: 0.03, 22: 0.02, 23: 0.01,
        }
    hours = list(hour_weights.keys())
    probs = np.array([hour_weights[h] for h in hours])
    probs = probs / probs.sum()
    return np.random.choice(hours, p=probs)


def generate_orders(n_days=90, orders_per_day_range=(60, 140)):
    """
    生成订单数据

    Parameters
    ----------
    n_days : int
        模拟天数
    orders_per_day_range : tuple
        每日订单数范围（工作日）

    Returns
    -------
    pd.DataFrame
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=n_days)

    # 生成顾客池
    n_customers = 500
    customer_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, n_customers + 1)]

    # 给顾客打标签（用于后续 RFM 分层）
    # 20% 高价值, 30% 普通, 30% 低频, 20% 沉睡
    customer_types = np.random.choice(
        ["high", "normal", "low", "dormant"],
        size=n_customers,
        p=[0.2, 0.3, 0.3, 0.2],
    )
    customer_type_map = dict(zip(customer_ids, customer_types))

    orders = []
    order_id_counter = 1

    for day_offset in range(n_days):
        date = start_date + timedelta(days=day_offset)
        is_weekend = 1 if date.weekday() >= 5 else 0

        # 周末订单量比工作日多 20%
        base_orders = np.random.randint(*orders_per_day_range)
        if is_weekend:
            base_orders = int(base_orders * 1.3)
            # 周末上午推迟，夜晚延长
            hour_weights = {
                0: 0.008, 1: 0.004, 2: 0.002, 3: 0.001,
                4: 0.001, 5: 0.002, 6: 0.005, 7: 0.008,
                8: 0.02, 9: 0.04, 10: 0.06, 11: 0.11,
                12: 0.12, 13: 0.07, 14: 0.04, 15: 0.03,
                16: 0.03, 17: 0.07, 18: 0.13, 19: 0.12,
                20: 0.07, 21: 0.04, 22: 0.03, 23: 0.02,
            }
        else:
            hour_weights = None  # 用默认

        # 节假日效应（模拟 5.1, 10.1 等节假日订单暴涨）
        if day_offset in [30, 31, 32]:  # 模拟一个小长假
            base_orders = int(base_orders * 1.8)

        n_today = base_orders

        for _ in range(n_today):
            hour = hour_sampler(hour_weights)
            minute = np.random.randint(0, 60)
            order_time = date.replace(
                hour=hour, minute=minute,
                second=np.random.randint(0, 60),
            )

            # 根据顾客类型抽样
            cust_type_probs = {
                "high": 0.35,    # 高价值顾客出现概率更高
                "normal": 0.25,
                "low": 0.15,
                "dormant": 0.05,
            }
            c_types = list(cust_type_probs.keys())
            c_probs = [cust_type_probs[t] for t in c_types]
            sampled_type = np.random.choice(c_types, p=np.array(c_probs) / sum(c_probs))

            # 从对应类型中随机选顾客
            available = [c for c, t in customer_type_map.items() if t == sampled_type]
            customer_id = np.random.choice(available)

            # 生成订单商品
            products = pick_products()

            # 平台
            platform = np.random.choice(
                list(PLATFORMS.keys()),
                p=list(PLATFORMS.values()),
            )

            for p_name in products:
                qty = np.random.choice([1, 1, 1, 1, 2, 2, 3], p=[0.4, 0.2, 0.15, 0.1, 0.07, 0.05, 0.03])
                unit_price = ALL_PRICES[p_name]
                total = unit_price * qty

                # 优惠（15% 概率）
                discount = 0.0
                if np.random.random() < 0.15:
                    discount = round(np.random.uniform(0.5, 5.0), 2)

                actual_amount = max(0, total - discount)

                # 退款（3% 概率）
                status = "completed"
                refund_amount = 0.0
                if np.random.random() < 0.03:
                    status = "refunded"
                    refund_amount = actual_amount

                orders.append({
                    "order_id": f"ORD{str(order_id_counter).zfill(8)}",
                    "order_time": order_time,
                    "date": order_time.strftime("%Y-%m-%d"),
                    "hour": hour,
                    "weekday": date.weekday(),
                    "is_weekend": is_weekend,
                    "customer_id": customer_id,
                    "platform": platform,
                    "product_name": p_name,
                    "category": PRODUCT_CATEGORY[p_name],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_amount": round(total, 2),
                    "discount": discount,
                    "actual_amount": round(actual_amount, 2),
                    "refund_amount": round(refund_amount, 2),
                    "status": status,
                })

            order_id_counter += 1

    df = pd.DataFrame(orders)
    return df


def generate_customer_profiles(orders_df):
    """从订单数据生成顾客画像表"""
    customer_stats = orders_df.groupby("customer_id").agg(
        total_orders=("order_id", "nunique"),
        total_spent=("actual_amount", "sum"),
        avg_order_value=("actual_amount", "mean"),
        first_order=("order_time", "min"),
        last_order=("order_time", "max"),
        favorite_category=("category", lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A"),
        platforms_used=("platform", lambda x: "|".join(x.unique())),
    ).reset_index()

    return customer_stats


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("[*] Generating mock data...")

    # 生成 90 天订单数据
    df_orders = generate_orders(n_days=90, orders_per_day_range=(80, 160))
    print(f"[+] Order details: {len(df_orders)} rows")

    # 生成顾客画像
    df_customers = generate_customer_profiles(df_orders)
    print(f"[+] Customer profiles: {len(df_customers)} customers")

    # 保存
    df_orders.to_csv("sample_orders.csv", index=False, encoding="utf-8-sig")
    df_customers.to_csv("sample_customers.csv", index=False, encoding="utf-8-sig")

    print("[*] Files saved:")
    print(f"    - sample_orders.csv ({df_orders['order_id'].nunique()} orders)")
    print(f"    - sample_customers.csv ({len(df_customers)} customers)")

    # 统计摘要
    print("\n[*] Data Summary:")
    print(f"    Date range: {df_orders['date'].min()} ~ {df_orders['date'].max()}")
    print(f"    Total revenue: ${df_orders['actual_amount'].sum():,.2f}")
    print(f"    Avg order value: ${df_orders.groupby('order_id')['actual_amount'].sum().mean():.2f}")
    print(f"    Refund rate: {len(df_orders[df_orders['status']=='refunded'])/len(df_orders)*100:.1f}%")
    print(f"    Platform distribution: {df_orders.groupby('platform')['order_id'].nunique().to_dict()}")

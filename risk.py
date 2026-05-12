def calculate_position(balance, risk_percent, price):

    risk_amount = balance * risk_percent

    position_size = risk_amount / price

    return round(position_size, 6)

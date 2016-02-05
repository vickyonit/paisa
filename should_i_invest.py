from datetime import datetime
from strategies import volatility_sd


def should_i_invest():
    if datetime.now().weekday() in [5, 6]:
        return False

    strategies = [volatility_sd]

    for strategy in strategies:
        strategy.run_strategy()

if __name__ == "__main__":
    print should_i_invest()
